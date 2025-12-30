import time
import asyncio
import os
import logging
from dotenv import load_dotenv
from src.agents.brain import AgentBrain
from src.data.models import AssetType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

async def run_simulation():
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY não encontrada. Configure no arquivo .env ou exporte a variável.")
        return

    logger.info("Inicializando Cérebro Compartilhado (Gemini)...")
    try:
        brain = AgentBrain()
    except Exception as e:
        logger.error(f"Erro ao conectar com LLM ou Redis: {e}")
        return

    await brain.memory_store.init_index()

    agents = [
        {
            "agent_id": "market_maker_01",
            "role": "Market Maker",
            "personality": "Conservador. Fornece liquidez mas evita grandes riscos. Gosta de spreads seguros.",
            "gold": 100000.0,
            "inventory": {AssetType.WOOD: 100, AssetType.FOOD: 100},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "market_maker_02",
            "role": "Market Maker",
            "personality": "Arrojado. Fornece liquidez e gosta de correr riscos. Gosta de spreads maiores.",
            "gold": 100000.0,
            "inventory": {AssetType.WOOD: 50, AssetType.FOOD: 50},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "trader_fomo",
            "role": "Speculator",
            "personality": "Impulsivo. Tem medo de ficar de fora (FOMO). Compra agressivamente se achar que vai subir.",
            "gold": 2500.0,
            "inventory": {AssetType.WOOD: 0, AssetType.FOOD: 0},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "trader_madhouse",
            "role": "Speculator",
            "personality": "Agressivo. Não tem medo de se arriscar. Compra barato se achar que vai subir, para vender caro. Procura a menor perda possível",
            "gold": 2000.0,
            "inventory": {AssetType.WOOD: 0, AssetType.FOOD: 0},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "farmer_john",
            "role": "Producer",
            "personality": "Pragmático. Produz FOOD e precisa vender para pagar contas. Vende a mercado se necessário.",
            "gold": 500.0,
            "inventory": {AssetType.WOOD: 10, AssetType.FOOD: 500},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "lamberjack_old_lemmy",
            "role": "Producer",
            "personality": "Conservador. Produz WOOD e precisa vender para pagar contas. Vende a mercado se necessário.",
            "gold": 500.0,
            "inventory": {AssetType.WOOD: 500, AssetType.FOOD: 10},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
    ]

    logger.info(f"Iniciando simulação com {len(agents)} agentes. Pressione Ctrl+C para parar.")

    try:
        while True:
            for agent_state in agents:
                logger.info(f"\nTurno: {agent_state['agent_id']} ({agent_state['role']})")

                try:
                    new_state = await brain.run_cycle(agent_state)
                    agent_state.update(new_state)

                    logger.info(f"Pensamento: {agent_state['thought_process']}")

                except Exception as e:
                    logger.error(f"Erro no turno do agente {agent_state['agent_id']}: {e}")

                await asyncio.sleep(3)

            logger.info("Aguardando próximo ciclo de rodadas...")
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        logger.info("Simulação interrompida pelo usuário.")

if __name__ == "__main__":
    asyncio.run(run_simulation())
