from typing import TypedDict, Annotated, List, Optional, Literal
from pydantic import BaseModel, Field
from src.data.models import AssetType, OrderSide, OrderType

class MarketObservation(TypedDict):
    best_bid: float
    best_ask: float
    last_price: float
    trend: str # up, down or flat

class AgentBrainState(TypedDict):
    # about the agent
    agent_id: str
    role: str
    personality: str
    
    # financial state
    inventory: dict[AssetType, int]
    gold: float
    
    # perception
    market_data: MarketObservation
    
    # reasoness
    thought_process: Optional[str]
    
    # decision
    chosen_action: Optional[str]
    order_details: Optional[dict]

class OrderDetails(BaseModel):
    asset: AssetType
    side: OrderSide
    type: OrderType = OrderType.LIMIT
    price: float
    quantity: int

class AgentDecision(BaseModel):
    thought_process: str = Field(description="Raciocínio estratégico curto sobre a decisão.")
    action: Literal["PLACE_ORDER", "WAIT"] = Field(description="Ação a ser tomada.")
    order_details: Optional[OrderDetails] = Field(description="Detalhes da ordem se a ação for PLACE_ORDER.")