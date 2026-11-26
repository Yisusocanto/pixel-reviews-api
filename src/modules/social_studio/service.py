import base64
import json
import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import inspect as sa_inspect

from src.core.settings import settings
from src.modules.games.models import Game
from src.modules.social_studio.repository import SocialStudioRepository
from src.modules.social_studio.schemas import (
    SlideKind,
    SocialAngle,
    SocialCandidateItem,
    SocialCandidatesResponse,
    SocialCaptions,
    SocialContentPack,
    SocialGenerateRequest,
    SocialLanguage,
    SocialSlide,
    StudioTtsRequest,
    StudioTtsResponse,
    VideoScene,
)
from src.services.gemini.client import GeminiService
from src.services.storage.client import StorageError, StorageService

logger = logging.getLogger("social_studio_service")

IGDB_SIZE_RE = re.compile(r"(/igdb/image/upload/)t_[a-z0-9_]+(/)", re.IGNORECASE)


def to_hd_jpg_url(url: str | None, preset: str = "t_1080p") -> str | None:
    if not url:
        return None
    updated = url
    if "images.igdb.com" in updated:
        updated = IGDB_SIZE_RE.sub(rf"\g<1>{preset}\g<2>", updated)
        updated = re.sub(r"\.webp(\?.*)?$", r".jpg\1", updated, flags=re.IGNORECASE)
    return updated


SOCIAL_PACK_JSON_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "topic_label": {"type": "STRING"},
        "hook_headline": {"type": "STRING"},
        "hook_subheadline": {"type": "STRING"},
        "voice_direction": {"type": "STRING"},
        "full_narration": {"type": "STRING"},
        "slides": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "kind": {
                        "type": "STRING",
                        "enum": ["hook", "spotlight", "comparison", "quote", "cta"],
                    },
                    "eyebrow": {"type": "STRING"},
                    "headline": {"type": "STRING"},
                    "body": {"type": "STRING"},
                    "badge": {"type": "STRING"},
                    "image_url": {"type": "STRING", "nullable": True},
                    "cover_url": {"type": "STRING", "nullable": True},
                    "critic_score": {"type": "INTEGER", "nullable": True},
                    "community_score": {"type": "NUMBER", "nullable": True},
                    "quote_author": {"type": "STRING", "nullable": True},
                },
                "required": ["kind", "eyebrow", "headline", "body", "badge"],
            },
        },
        "video_scenes": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "headline": {"type": "STRING"},
                    "narration": {"type": "STRING"},
                    "badge": {"type": "STRING"},
                    "image_url": {"type": "STRING", "nullable": True},
                    "cover_url": {"type": "STRING", "nullable": True},
                    "critic_score": {"type": "INTEGER", "nullable": True},
                    "community_score": {"type": "NUMBER", "nullable": True},
                    "duration_seconds": {"type": "NUMBER"},
                },
                "required": ["headline", "narration", "badge", "duration_seconds"],
            },
        },
        "captions": {
            "type": "OBJECT",
            "properties": {
                "tiktok": {"type": "STRING"},
                "instagram": {"type": "STRING"},
                "x_post": {"type": "STRING"},
                "youtube_shorts": {"type": "STRING"},
                "reddit_title": {"type": "STRING"},
                "reddit_body": {"type": "STRING"},
            },
            "required": [
                "tiktok",
                "instagram",
                "x_post",
                "youtube_shorts",
                "reddit_title",
                "reddit_body",
            ],
        },
    },
    "required": [
        "topic_label",
        "hook_headline",
        "hook_subheadline",
        "voice_direction",
        "full_narration",
        "slides",
        "video_scenes",
        "captions",
    ],
}


class SocialStudioService:
    def __init__(
        self,
        repo: SocialStudioRepository,
        gemini: GeminiService,
        storage: StorageService,
    ) -> None:
        self.repo = repo
        self.gemini = gemini
        self.storage = storage

    async def list_candidates(
        self, angle: SocialAngle, limit: int = 12
    ) -> SocialCandidatesResponse:
        items: list[SocialCandidateItem] = []

        if angle == SocialAngle.UNFILTERED_REVIEW:
            reviews = await self.repo.get_featured_reviews(limit=limit)
            for review, likes_count in reviews:
                if not review.game:
                    continue
                backdrop = (
                    review.game.background_image
                    or (review.game.screenshots[0] if review.game.screenshots else None)
                    or review.game.image_url
                )
                items.append(
                    SocialCandidateItem(
                        angle=angle,
                        game_id=review.game.id,
                        game_slug=review.game.slug,
                        game_title=review.game.title,
                        cover_url=to_hd_jpg_url(review.game.image_url, "t_cover_big_2x")
                        or review.game.image_url,
                        backdrop_url=to_hd_jpg_url(backdrop, "t_1080p"),
                        critic_score=review.game.critic_score,
                        community_score=float(review.score),
                        total_reviews=1,
                        review_id=review.id,
                        review_title=review.title,
                        review_excerpt=(review.content or "")[:180],
                        reviewer_username=review.user.username if review.user else "player",
                        summary_badge=f"{review.score}★ • {likes_count} likes",
                    )
                )
            return SocialCandidatesResponse(angle=angle, items=items)

        if angle == SocialAngle.MOST_ANTICIPATED:
            wanted_rows = await self.repo.get_most_anticipated_games(limit=limit)
            for game, wish_count in wanted_rows:
                backdrop = (
                    game.background_image
                    or (game.screenshots[0] if game.screenshots else None)
                    or game.image_url
                )
                items.append(
                    SocialCandidateItem(
                        angle=angle,
                        game_id=game.id,
                        game_slug=game.slug,
                        game_title=game.title,
                        cover_url=to_hd_jpg_url(game.image_url, "t_cover_big_2x") or game.image_url,
                        backdrop_url=to_hd_jpg_url(backdrop, "t_1080p"),
                        critic_score=game.critic_score,
                        wishlist_count=wish_count,
                        summary_badge=f"{wish_count} wishlists",
                    )
                )
            return SocialCandidatesResponse(angle=angle, items=items)

        if angle == SocialAngle.HIDDEN_GEMS:
            gem_rows = await self.repo.get_hidden_gem_games(limit=limit)
            for game, avg_score, reviews_count in gem_rows:
                backdrop = (
                    game.background_image
                    or (game.screenshots[0] if game.screenshots else None)
                    or game.image_url
                )
                badge_score = f"{game.critic_score}/100" if game.critic_score else "Gem"
                items.append(
                    SocialCandidateItem(
                        angle=angle,
                        game_id=game.id,
                        game_slug=game.slug,
                        game_title=game.title,
                        cover_url=to_hd_jpg_url(game.image_url, "t_cover_big_2x") or game.image_url,
                        backdrop_url=to_hd_jpg_url(backdrop, "t_1080p"),
                        critic_score=game.critic_score,
                        community_score=round(float(avg_score), 1) if avg_score else None,
                        total_reviews=reviews_count,
                        summary_badge=f"Critic {badge_score} • {reviews_count} logs",
                    )
                )
            return SocialCandidatesResponse(angle=angle, items=items)

        rows = await self.repo.get_games_with_community_stats(limit=limit * 2)
        scored_rows: list[tuple[float, Game, float | None, int]] = []
        for game, avg_score, reviews_count in rows:
            gap = 0.0
            if game.critic_score is not None and avg_score is not None:
                gap = abs((game.critic_score / 20.0) - float(avg_score))
            scored_rows.append((gap, game, avg_score, reviews_count))

        scored_rows.sort(key=lambda entry: (entry[0], entry[3]), reverse=True)
        for _, game, avg_score, reviews_count in scored_rows[:limit]:
            backdrop = (
                game.background_image
                or (game.screenshots[0] if game.screenshots else None)
                or game.image_url
            )
            comm_txt = f"{float(avg_score):.1f}★" if avg_score is not None else "Sin nota"
            crit_txt = f"{game.critic_score}/100" if game.critic_score is not None else "N/A"
            items.append(
                SocialCandidateItem(
                    angle=angle,
                    game_id=game.id,
                    game_slug=game.slug,
                    game_title=game.title,
                    cover_url=to_hd_jpg_url(game.image_url, "t_cover_big_2x") or game.image_url,
                    backdrop_url=to_hd_jpg_url(backdrop, "t_1080p"),
                    critic_score=game.critic_score,
                    community_score=round(float(avg_score), 1) if avg_score is not None else None,
                    total_reviews=reviews_count,
                    summary_badge=f"Prensa {crit_txt} vs {comm_txt}",
                )
            )
        return SocialCandidatesResponse(angle=angle, items=items)

    async def generate_pack(self, data: SocialGenerateRequest) -> SocialContentPack:
        context_payload = await self._build_factual_context(data)

        lang_instruction = (
            "Escribe TODO en español gamer moderno, natural, afilado y con personalidad "
            "(sirve para LATAM y España, cero traducciones robóticas, cero frases cliché como "
            "'En el vertiginoso mundo de los videojuegos' o 'Sumérgete')."
            if data.language == SocialLanguage.ES
            else "Write EVERYTHING in sharp, culturally fluent gamer English with zero generic AI clichés."
        )

        system_instruction = (
            "Eres el director creativo editorial de Pixel Reviews (www.pixelreviews.app), "
            "la plataforma donde los jugadores califican videojuegos sin filtros corporativos. "
            f"{lang_instruction} "
            "REGLAS ESTRICTAS:\n"
            "1. Usa ÚNICAMENTE las URLs exactas `cover_url` y `screenshots`/`backdrop_url` entregadas en los datos reales.\n"
            "2. Genera entre 5 y 6 slides para carrusel 1080x1350: el primero `kind='hook'`, "
            "los intermedios con datos/comparativas/citas reales y el último `kind='cta'` invitando a "
            "dejar su veredicto en pixelreviews.app.\n"
            "3. Genera entre 4 y 6 `video_scenes` para un Short/Reel vertical de 30-42 segundos en total, "
            "donde `full_narration` sea la unión fluida de todas las escenas y empiece con un gancho "
            "imposible de ignorar en los primeros 3 segundos.\n"
            "4. En `reddit_title` y `reddit_body`, plantea un debate genuino para gamers (sin sonar a anuncio publicitario)."
        )

        user_prompt = (
            f"Ángulo solicitado: {data.angle.value}\n"
            f"Tono editorial: {data.editorial_tone}\n"
            f"Idioma: {data.language.value}\n\n"
            f"DATOS REALES DE PIXEL REVIEWS / IGDB:\n"
            f"{json.dumps(context_payload, ensure_ascii=False, indent=2)}"
        )

        raw = await self.gemini.generate_structured_json(
            prompt=user_prompt,
            system_instruction=system_instruction,
            response_schema=SOCIAL_PACK_JSON_SCHEMA,
            temperature=0.82,
        )

        slides = [
            SocialSlide(
                kind=SlideKind(s.get("kind", "spotlight")),
                eyebrow=s["eyebrow"],
                headline=s["headline"],
                body=s["body"],
                badge=s.get("badge", ""),
                image_url=to_hd_jpg_url(s.get("image_url"), "t_1080p"),
                cover_url=to_hd_jpg_url(s.get("cover_url"), "t_cover_big_2x"),
                critic_score=s.get("critic_score"),
                community_score=s.get("community_score"),
                quote_author=s.get("quote_author"),
            )
            for s in raw.get("slides", [])
        ]

        video_scenes = [
            VideoScene(
                headline=v["headline"],
                narration=v["narration"],
                badge=v.get("badge", ""),
                image_url=to_hd_jpg_url(v.get("image_url"), "t_1080p"),
                cover_url=to_hd_jpg_url(v.get("cover_url"), "t_cover_big_2x"),
                critic_score=v.get("critic_score"),
                community_score=v.get("community_score"),
                duration_seconds=max(3.0, float(v.get("duration_seconds", 6.0))),
            )
            for v in raw.get("video_scenes", [])
        ]

        return SocialContentPack(
            angle=data.angle,
            language=data.language,
            topic_label=raw["topic_label"],
            hook_headline=raw["hook_headline"],
            hook_subheadline=raw["hook_subheadline"],
            voice_direction=raw["voice_direction"],
            full_narration=raw["full_narration"],
            slides=slides,
            video_scenes=video_scenes,
            captions=SocialCaptions(**raw["captions"]),
        )

    async def synthesize_voiceover(self, data: StudioTtsRequest) -> StudioTtsResponse:
        selected_voice = data.voice_name or self.gemini.default_voice
        wav_bytes, duration_seconds = await self.gemini.generate_studio_tts(
            narration_text=data.narration,
            voice_direction=data.voice_direction,
            voice_name=selected_voice,
        )

        encoded_b64 = base64.b64encode(wav_bytes).decode("ascii")
        audio_data_url = f"data:audio/wav;base64,{encoded_b64}"

        public_audio_url: str | None = None
        object_key = f"social-studio/tts/{uuid.uuid7()}.wav"
        try:
            await self.storage.upload(object_key, wav_bytes, "audio/wav", "public, max-age=86400")
            if settings.CF_PUBLIC_URL:
                public_audio_url = f"{settings.CF_PUBLIC_URL.rstrip('/')}/{object_key}"
        except StorageError:
            logger.warning(
                "[SOCIAL_STUDIO] Could not upload TTS WAV to R2; serving inline data URL"
            )

        return StudioTtsResponse(
            audio_url=public_audio_url,
            audio_data_url=audio_data_url,
            duration_seconds=duration_seconds,
            voice_name=selected_voice,
            model=self.gemini.tts_model,
        )

    async def _build_factual_context(self, data: SocialGenerateRequest) -> dict[str, Any]:
        if data.review_id:
            review = await self.repo.get_review_by_id(data.review_id)
            if not review or not review.game:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target review not found",
                )
            game = review.game
            return {
                "mode": "single_review_spotlight",
                "review": {
                    "score": review.score,
                    "title": review.title,
                    "content": review.content,
                    "author": f"@{review.user.username}" if review.user else "@player",
                },
                "game": self._serialize_game_assets(game),
            }

        if data.game_slug:
            row = await self.repo.get_game_by_slug_with_stats(data.game_slug)
            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target game not found",
                )
            game, avg_score, reviews_count = row
            return {
                "mode": "single_game_deep_dive",
                "game": {
                    **self._serialize_game_assets(game),
                    "community_score": round(float(avg_score), 2) if avg_score else None,
                    "total_reviews": reviews_count,
                },
            }

        candidates = await self.list_candidates(angle=data.angle, limit=5)
        if not candidates.items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No games or reviews available in the database to generate content",
            )

        enriched_items: list[dict[str, Any]] = []
        for item in candidates.items[:5]:
            row = await self.repo.get_game_by_slug_with_stats(item.game_slug)
            game_assets = self._serialize_game_assets(row[0]) if row else {}
            enriched_items.append(
                {
                    **item.model_dump(mode="json"),
                    "game_details": game_assets,
                }
            )

        return {
            "mode": "curated_multi_item",
            "angle": data.angle.value,
            "items": enriched_items,
        }

    @staticmethod
    def _serialize_game_assets(game: Game) -> dict[str, Any]:
        unloaded = sa_inspect(game).unloaded
        genres = [] if "genres" in unloaded else [g.name for g in (game.genres or [])]
        developers = [] if "developers" in unloaded else [d.name for d in (game.developers or [])]
        platforms = [] if "platforms" in unloaded else [p.name for p in (game.platforms or [])]

        screenshots = [
            converted
            for s in (game.screenshots or [])[:5]
            if (converted := to_hd_jpg_url(s, "t_1080p")) is not None
        ]
        backdrop = to_hd_jpg_url(
            game.background_image or (game.screenshots[0] if game.screenshots else game.image_url),
            "t_1080p",
        )
        return {
            "title": game.title,
            "slug": game.slug,
            "release_year": game.release_date.year if game.release_date else None,
            "description": (game.description or "")[:600],
            "critic_score": game.critic_score,
            "genres": genres,
            "developers": developers,
            "platforms": platforms,
            "cover_url": to_hd_jpg_url(game.image_url, "t_cover_big_2x"),
            "backdrop_url": backdrop,
            "screenshots": screenshots,
        }
