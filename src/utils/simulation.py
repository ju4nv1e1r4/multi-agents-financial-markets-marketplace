import time
import os
import logging
from dotenv import load_dotenv
from src.agents.brain import AgentBrain
from src.data.models import AssetType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

def run_simulation():
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY não encontrada. Configure no arquivo .env.")
        return

    logger.info("Inicializando Cérebro Compartilhado...")
    try:
        brain = AgentBrain()
    except Exception as e:
        logger.error(f"Erro ao conectar com LLM ou Redis: {e}")
        return

    agents = [
        {
            "agent_id": "market_maker_01",
            "role": "Market Maker",
            "personality": "Conservador. Fornece liquidez mas evita grandes riscos. Gosta de spreads seguros.",
            "gold": 10000.0,
            "inventory": {AssetType.WOOD: 100, AssetType.FOOD: 100},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        },
        {
            "agent_id": "trader_fomo",
            "role": "Speculator",
            "personality": "Impulsivo. Tem medo de ficar de fora (FOMO). Compra agressivamente se achar que vai subir.",
            "gold": 2000.0,
            "inventory": {AssetType.WOOD: 0, AssetType.FOOD: 0},
            "market_data": {"best_bid": 0, "best_ask": 0, "last_price": 0, "trend": "flat"},
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
            "thought_process": None,
            "chosen_action": None,
            "order_details": None
        }
    ]

    logger.info(f"Iniciando simulação com {len(agents)} agentes. Pressione Ctrl+C para parar.")

    try:
        while True:
            for agent_state in agents:
                logger.info(f"\nTurno: {agent_state['agent_id']} ({agent_state['role']})")
                
                try:
                    new_state = brain.run_cycle(agent_state)
                    agent_state.update(new_state)
                    logger.info(f"Pensamento: {agent_state['thought_process']}")
                    
                except Exception as e:
                    logger.error(f"Erro no turno do agente {agent_state['agent_id']}: {e}")

                time.sleep(3)
            
            logger.info("Aguardando próximo ciclo de rodadas...")
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Simulação interrompida pelo usuário.")

if __name__ == "__main__":
    run_simulation()
