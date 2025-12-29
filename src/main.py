import asyncio
from src.engine.service import MarketService

if __name__ == "__main__":
    service = MarketService()
    asyncio.run(service.start())
