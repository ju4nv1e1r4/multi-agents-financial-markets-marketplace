import asyncio
import logging
import os
import json
from redis.asyncio import Redis
from src.data.models import Order, Trade
from src.engine.exchange import Exchange

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class MarketService:
    def __init__(self):
        self.redis = Redis.from_url(REDIS_URL, decode_responses=True)
        self.exchange = Exchange()
        self.pubsub = self.redis.pubsub()

    async def start(self):
        """Inicia o loop principal de consumo de mensagens."""
        logger.info(f"Market Engine iniciando... Conectado em {REDIS_URL}")

        await self.pubsub.subscribe("market:orders")
        logger.info("📡 Escutando canal 'market:orders'...")

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    await self.process_message(message["data"])
        except asyncio.CancelledError:
            logger.info("Serviço interrompido.")
        except Exception as e:
            logger.error(f"Erro crítico no loop: {e}", exc_info=True)
        finally:
            await self.redis.close()

    async def process_message(self, data: str):
        """Desserializa a ordem e executa no Engine."""
        try:
            order = Order.model_validate_json(data)
            logger.info(f"Ordem Recebida: {order.side.value} {order.quantity} {order.asset.value} @ ${order.price} (Agent: {order.agent_id})")

            trades = self.exchange.process_order(order)

            if trades:
                await self.publish_trades(trades)
            
            # NOTE: For my-self, to remember if necessary
            # Snapshot do Book persistance on Redis (failures recovery):
            # await self.snapshot_book(order.asset)

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {data} | Erro: {e}")

    async def publish_trades(self, trades: list[Trade]):
        """Publica os trades executados para o Ticker."""
        for trade in trades:
            trade_json = trade.model_dump_json()

            await self.redis.publish("market:ticker", trade_json)
            
            logger.info(f"TRADE EXECUTADO: {trade.quantity} {trade.asset.value} @ ${trade.price} ({trade.buyer_agent_id} -> {trade.seller_agent_id})")

if __name__ == "__main__":
    try:
        service = MarketService()
        asyncio.run(service.start())
    except KeyboardInterrupt:
        pass
