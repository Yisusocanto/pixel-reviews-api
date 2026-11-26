import uuid
from enum import StrEnum

from pydantic import Field

from src.schemas.config_base import ConfigBase


class SocialAngle(StrEnum):
    CRITIC_VS_PLAYERS = "critic_vs_players"
    UNFILTERED_REVIEW = "unfiltered_review"
    HIDDEN_GEMS = "hidden_gems"
    MOST_ANTICIPATED = "most_anticipated"


class SocialLanguage(StrEnum):
    ES = "es"
    EN = "en"


class SlideKind(StrEnum):
    HOOK = "hook"
    SPOTLIGHT = "spotlight"
    COMPARISON = "comparison"
    QUOTE = "quote"
    CTA = "cta"


class SocialCandidateItem(ConfigBase):
    angle: SocialAngle
    game_id: uuid.UUID
    game_slug: str
    game_title: str
    cover_url: str
    backdrop_url: str | None = None
    critic_score: int | None = None
    community_score: float | None = None
    total_reviews: int = 0
    wishlist_count: int = 0
    review_id: uuid.UUID | None = None
    review_title: str | None = None
    review_excerpt: str | None = None
    reviewer_username: str | None = None
    summary_badge: str


class SocialCandidatesResponse(ConfigBase):
    angle: SocialAngle
    items: list[SocialCandidateItem]


class SocialSlide(ConfigBase):
    kind: SlideKind
    eyebrow: str
    headline: str
    body: str
    badge: str = ""
    image_url: str | None = None
    cover_url: str | None = None
    critic_score: int | None = None
    community_score: float | None = None
    quote_author: str | None = None


class VideoScene(ConfigBase):
    headline: str
    narration: str
    badge: str = ""
    image_url: str | None = None
    cover_url: str | None = None
    critic_score: int | None = None
    community_score: float | None = None
    duration_seconds: float = 6.0


class SocialCaptions(ConfigBase):
    tiktok: str
    instagram: str
    x_post: str
    youtube_shorts: str
    reddit_title: str
    reddit_body: str


class SocialGenerateRequest(ConfigBase):
    angle: SocialAngle
    language: SocialLanguage = SocialLanguage.ES
    game_slug: str | None = None
    review_id: uuid.UUID | None = None
    editorial_tone: str = Field(default="editorial_gamer", max_length=80)


class SocialContentPack(ConfigBase):
    angle: SocialAngle
    language: SocialLanguage
    topic_label: str
    hook_headline: str
    hook_subheadline: str
    voice_direction: str
    full_narration: str
    slides: list[SocialSlide]
    video_scenes: list[VideoScene]
    captions: SocialCaptions


class StudioTtsRequest(ConfigBase):
    narration: str = Field(min_length=10, max_length=4500)
    voice_direction: str = Field(
        default=(
            "Habla como un creador de contenido gamer apasionado y con criterio, "
            "ritmo ágil, entonación natural y énfasis dramático en los remates."
        ),
        max_length=600,
    )
    voice_name: str | None = Field(default=None, max_length=40)


class StudioTtsResponse(ConfigBase):
    audio_url: str | None = None
    audio_data_url: str
    duration_seconds: float
    voice_name: str
    model: str
