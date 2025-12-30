import time
import asyncio
import os
import logging
from dotenv import load_dotenv
from redis.asyncio import Redis
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

    redis_control = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

    await brain.memory_store.init_index()

    agents = []
    roles_config = [
        ("Market Maker", "Conservador. Fornece liquidez.", 100000.0),
        ("Speculator", "Agressivo (FOMO).", 5000.0),
        ("Producer", "Pragmático. Vende para pagar contas.", 1000.0),
        ("Value Investor", "Analítico. Compra na baixa.", 10000.0)
    ]

    for i in range(1, 21):
        role, persona, gold = roles_config[i % len(roles_config)]
        agents.append({
            "agent_id": f"agent_{i:02d}_{role.replace(' ', '_').lower()}",
            "role": role,
            "personality": persona,
            "gold": gold,
            "inventory": {AssetType.WOOD: 50, AssetType.FOOD: 50},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "memories": "",
            "breaking_news": None,
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        })

    logger.info(f"Iniciando simulação com {len(agents)} agentes. Pressione Ctrl+C para parar.")

    try:
        while True:
            status = await redis_control.get("system:status")
            if status == "PAUSED":
                logger.info("Simulação PAUSADA pelo Painel de Controle.")
                await asyncio.sleep(2)
                continue

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
