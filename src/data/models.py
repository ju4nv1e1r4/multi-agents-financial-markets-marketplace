from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime
from decimal import Decimal


class OrderSide(str, Enum):
    BID = "BID" # buy
    ASK = "ASK" # sell

class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class AssetType(str, Enum):
    WOOD = "WOOD"
    FOOD = "FOOD"
    IRON = "IRON"
    GOLD = "GOLD"
    DOLAR = "DOLAR"

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    asset: AssetType
    side: OrderSide
    type: OrderType = OrderType.LIMIT
    price: Decimal = Field(..., gt=0) # price > 0
    quantity: int = Field(..., gt=0) # qty > 0
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        frozen = True # immutable

class Trade(BaseModel):
    """Representa uma transação executada (O 'Match')"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buyer_agent_id: str
    seller_agent_id: str
    asset: AssetType
    price: Decimal
    quantity: int
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentState(BaseModel):
    agent_id: str
    role: str
    inventory: dict[AssetType, int]
    gold_balance: Decimal
    dolar_balance: Decimal
    personality: str
