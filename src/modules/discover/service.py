from src.modules.discover.repository import DiscoverRepository
from src.modules.discover.schemas import (
    Statistics,
    TopRatedGame,
    TopReviewedGame,
    TopWantedGame,
    TotalReviews,
    UserWithReviewCount,
)


class DiscoverService:
    def __init__(self, repo: DiscoverRepository):
        self.repo = repo

    async def statistics(self) -> Statistics:
        top_rated_games = await self.repo.top_rated_games()
        top_wanted_games = await self.repo.top_wanted_games()
        top_reviewed_games = await self.repo.top_reviewed_games()
        users_with_the_most_reviews = await self.repo.user_with_the_most_reviews()
        total_reviews = await self.repo.reviews_amount()

        return Statistics(
            top_rated_games=[
                TopRatedGame(game=data[0], average=data[1], count=data[2])
                for data in top_rated_games
            ],
            top_reviewed_games=[
                TopReviewedGame(game=data[0], count=data[1], last_week=data[2])
                for data in top_reviewed_games
            ],
            top_wanted_games=[
                TopWantedGame(game=data[0], count=data[1]) for data in top_wanted_games
            ],
            top_users_with_the_most_reviews=[
                UserWithReviewCount(user=data[0], count=data[1], last_week=data[2])
                for data in users_with_the_most_reviews
            ],
            total_reviews=TotalReviews(total=total_reviews[0], last_week=total_reviews[1]),
        )
