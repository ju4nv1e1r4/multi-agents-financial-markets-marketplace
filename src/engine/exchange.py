import heapq
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field
from decimal import Decimal

from src.data.models import Order, Trade, OrderSide, AssetType, OrderType

@dataclass(order=True)
class AskEntry:
    """
    Wrapper for Sell Orders (Asks) in the Min-Heap.
    Sorting: Lowest Price first, then Earliest Timestamp.
    """
    price: Decimal
    timestamp: datetime
    order: Order = field(compare=False)
    remaining_qty: int = field(compare=False)

@dataclass(order=True)
class BidEntry:
    """
    Wrapper for Buy Orders (Bids) in the Max-Heap.
    Sorting: Highest Price first (via neg_price), then Earliest Timestamp.
    """
    neg_price: Decimal
    timestamp: datetime
    order: Order = field(compare=False)
    remaining_qty: int = field(compare=False)

class OrderBook:
    def __init__(self, asset: AssetType):
        self.asset = asset
        self.bids: List[BidEntry] = []
        self.asks: List[AskEntry] = []

    def process_order(self, order: Order) -> List[Trade]:
        """
        Processes an incoming order against the Limit Order Book (LOB).
        Returns a list of executed Trades.
        """
        trades = []
        remaining_qty = order.quantity

        match_price = order.price
        if order.type == OrderType.MARKET:
            if order.side == OrderSide.BID:
                match_price = Decimal('Infinity')
            else:
                match_price = Decimal('0')

        if order.side == OrderSide.BID:
            while remaining_qty > 0 and self.asks:
                best_ask = self.asks[0]

                if best_ask.order.agent_id == order.agent_id:
                    heapq.heappop(self.asks)
                    continue

                if match_price >= best_ask.price:
                    exec_qty = min(remaining_qty, best_ask.remaining_qty)
                    exec_price = best_ask.price

                    trade = Trade(
                        buyer_agent_id=order.agent_id,
                        seller_agent_id=best_ask.order.agent_id,
                        asset=self.asset,
                        price=exec_price,
                        quantity=exec_qty,
                        timestamp=datetime.now()
                    )
                    trades.append(trade)

                    remaining_qty -= exec_qty
                    best_ask.remaining_qty -= exec_qty

                    if best_ask.remaining_qty == 0:
                        heapq.heappop(self.asks)
                else:
                    break

            if remaining_qty > 0 and order.type == OrderType.LIMIT:
                entry = BidEntry(
                    neg_price=-order.price,
                    timestamp=order.timestamp,
                    order=order,
                    remaining_qty=remaining_qty
                )
                heapq.heappush(self.bids, entry)

        else:
            while remaining_qty > 0 and self.bids:
                best_bid = self.bids[0]
                best_bid_price = -best_bid.neg_price

                # Self-Trading Prevention
                if best_bid.order.agent_id == order.agent_id:
                    heapq.heappop(self.bids)
                    continue

                if match_price <= best_bid_price:
                    exec_qty = min(remaining_qty, best_bid.remaining_qty)
                    exec_price = best_bid_price

                    trade = Trade(
                        buyer_agent_id=best_bid.order.agent_id,
                        seller_agent_id=order.agent_id,
                        asset=self.asset,
                        price=exec_price,
                        quantity=exec_qty,
                        timestamp=datetime.now()
                    )
                    trades.append(trade)

                    remaining_qty -= exec_qty
                    best_bid.remaining_qty -= exec_qty

                    if best_bid.remaining_qty == 0:
                        heapq.heappop(self.bids)
                else:
                    break

            if remaining_qty > 0 and order.type == OrderType.LIMIT:
                entry = AskEntry(
                    price=order.price,
                    timestamp=order.timestamp,
                    order=order,
                    remaining_qty=remaining_qty
                )
                heapq.heappush(self.asks, entry)

        return trades

class Exchange:
    def __init__(self):
        self.books: Dict[AssetType, OrderBook] = {
            asset: OrderBook(asset) for asset in AssetType
        }

    def process_order(self, order: Order) -> List[Trade]:
        """Route the order to the correct asset book."""
        return self.books[order.asset].process_order(order)
