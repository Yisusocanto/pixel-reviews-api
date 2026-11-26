from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.auth.dependencies import AdminRequiredDep
from src.modules.social_studio.dependencies import SocialStudioServiceDep
from src.modules.social_studio.schemas import (
    SocialAngle,
    SocialCandidatesResponse,
    SocialContentPack,
    SocialGenerateRequest,
    StudioTtsRequest,
    StudioTtsResponse,
)

router = APIRouter(
    prefix="/admin/social",
    tags=["Admin Social Studio"],
)


@router.get("/candidates", response_model=SocialCandidatesResponse)
async def get_social_candidates(
    _admin: AdminRequiredDep,
    service: SocialStudioServiceDep,
    angle: Annotated[SocialAngle, Query()] = SocialAngle.CRITIC_VS_PLAYERS,
    limit: Annotated[int, Query(ge=1, le=24)] = 12,
):
    return await service.list_candidates(angle=angle, limit=limit)


@router.post("/generate", response_model=SocialContentPack)
async def generate_social_pack(
    _admin: AdminRequiredDep,
    service: SocialStudioServiceDep,
    data: SocialGenerateRequest,
):
    return await service.generate_pack(data)


@router.post("/tts", response_model=StudioTtsResponse)
async def generate_studio_voiceover(
    _admin: AdminRequiredDep,
    service: SocialStudioServiceDep,
    data: StudioTtsRequest,
):
    return await service.synthesize_voiceover(data)
