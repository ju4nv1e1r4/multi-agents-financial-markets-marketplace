import asyncio
import os
from redis.asyncio import Redis
from src.engine.service import MarketService
from src.engine.news import broadcast_news

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

async def main():
    redis_news = Redis.from_url(REDIS_URL, decode_responses=True)
    service = MarketService()
    
    await asyncio.gather(
        service.start(),
        broadcast_news(redis_news)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
