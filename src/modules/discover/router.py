from fastapi import APIRouter

from src.modules.discover.dependencies import DiscoverServiceDep
from src.modules.discover.schemas import Statistics

router = APIRouter(
    prefix="/discover",
    tags=["Discover"],
)


@router.get("", response_model=Statistics)
async def get_statistics(service: DiscoverServiceDep):
    return await service.statistics()
