import json
import logging
import os
from typing import Literal
from decimal import Decimal
import redis

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.data.models import OrderSide, AssetType
from src.agents.models import AgentBrainState
from src.agents.models import AgentDecision
from src.infra.memory_store import MemoryStore

logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class AgentBrain:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        api_key = os.getenv("GOOGLE_API_KEY")
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            api_key=api_key,
            temperature=0.7
        )
        self.memory_store = MemoryStore(
            redis_url=REDIS_URL,
            api_key=api_key
        )
        self.structured_llm = self.llm.with_structured_output(AgentDecision) 
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentBrainState)

        workflow.add_node("perceive", self.perceive_market)
        workflow.add_node("reason", self.generate_strategy)
        workflow.add_node("act", self.execute_order)

        workflow.set_entry_point("perceive")
        workflow.add_edge("perceive", "reason")
        workflow.add_edge("reason", "act")
        workflow.add_edge("act", END)

        return workflow.compile()

    async def perceive_market(self, state: AgentBrainState):
        logger.info(f"{state['agent_id']} observando mercado...")

        last_trade_json = self.redis.get("market:last_trade")
        
        market_obs = state["market_data"]
        
        if last_trade_json:
            try:
                trade_data = json.loads(last_trade_json)
                market_obs["last_price"] = float(trade_data.get("price", 0))
            except Exception as e:
                logger.warning(f"Erro ao ler market data: {e}")

        query_context = f"Market Trend: {market_obs.get('trend', 'flat')}. Last Price: {market_obs.get('last_price')}"
        memories = await self.memory_store.recall_memories(state['agent_id'], query_context)
        
        state["market_data"] = market_obs
        state["memories"] = memories
        return state

    async def generate_strategy(self, state: AgentBrainState):
        """LLM central"""
        logger.info(f"{state['agent_id']} pensando...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é {role} com personalidade {personality}."),
            ("human", """
            STATUS ATUAL:
            - Ouro: {gold}
            - Inventário: {inventory}
            - Mercado: {market_data}
            
            MEMÓRIAS (Lições do Passado):
            {memories}

            Qual sua próxima jogada?
            """)
        ])

        chain = prompt | self.structured_llm
        decision: AgentDecision = await chain.ainvoke(state)

        return {
            "thought_process": decision.thought_process,
            "chosen_action": decision.action,
            "order_details": decision.order_details.model_dump() if decision.order_details else None
        }

    async def execute_order(self, state: AgentBrainState):
        """Execução e Validação"""
        action = state.get("chosen_action")
        
        if action == "PLACE_ORDER" and state.get("order_details"):
            details = state["order_details"]

            if details["side"] == "BID":
                total_cost = Decimal(str(details["price"])) * details["quantity"]
                if state["gold"] < float(total_cost):
                    logger.warning(f"{state['agent_id']} Saldo Insuficiente! Tem ${state['gold']}, precisa ${total_cost}")
                    return state

            elif details["side"] == "ASK":
                asset = details["asset"]
                current_qty = state["inventory"].get(asset, 0) # type: ignore
                if current_qty < details["quantity"]:
                    logger.warning(f"{state['agent_id']} Estoque Insuficiente de {asset}! Tem {current_qty}, quer vender {details['quantity']}")
                    return state

            order_payload = {
                "agent_id": state["agent_id"],
                "asset": details["asset"],
                "side": details["side"],
                "type": details["type"],
                "price": details["price"],
                "quantity": details["quantity"],
            }
            self.redis.publish("market:orders", json.dumps(order_payload))
            logger.info(f"{state['agent_id']} ENVIOU ORDEM: {details['side']} {details['quantity']} {details['asset']} @ {details['price']}")

            memory_content = f"Cenário: {state['market_data']}. Ação: {action} {details['side']} {details['asset']}. Motivo: {state['thought_process']}"
            await self.memory_store.save_memory(state['agent_id'], memory_content)
            
        else:
            logger.info(f"{state['agent_id']} decidiu esperar.")
            
        return state

    async def run_cycle(self, initial_state: AgentBrainState):
        return await self.graph.ainvoke(initial_state)
