import heapq
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field

from src.data.models import Order, Trade, OrderSide, AssetType

@dataclass(order=True)
class AskEntry:
    """
    Wrapper for Sell Orders (Asks) in the Min-Heap.
    Sorting: Lowest Price first, then Earliest Timestamp.
    """
    price: float
    timestamp: datetime
    order: Order = field(compare=False)
    remaining_qty: int = field(compare=False)

@dataclass(order=True)
class BidEntry:
    """
    Wrapper for Buy Orders (Bids) in the Max-Heap.
    Sorting: Highest Price first (via neg_price), then Earliest Timestamp.
    """
    neg_price: float
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

        if order.side == OrderSide.BID:
            # BUY ORDER: Match against Asks (Lowest Sellers)
            while remaining_qty > 0 and self.asks:
                best_ask = self.asks[0] # Peek at best offer (O(1))

                # Check Price Condition: Buy Price >= Sell Price
                if order.price >= best_ask.price:
                    # EXECUTION (Match)
                    exec_qty = min(remaining_qty, best_ask.remaining_qty)
                    exec_price = best_ask.price # Maker's price

                    trade = Trade(
                        buyer_agent_id=order.agent_id,
                        seller_agent_id=best_ask.order.agent_id,
                        asset=self.asset,
                        price=exec_price,
                        quantity=exec_qty,
                        timestamp=datetime.now()
                    )
                    trades.append(trade)

                    # Update quantities
                    remaining_qty -= exec_qty
                    best_ask.remaining_qty -= exec_qty

                    # Remove filled orders from the book
                    if best_ask.remaining_qty == 0:
                        heapq.heappop(self.asks)
                else:
                    # No overlap in price, stop matching
                    break
            
            # RESTING: If quantity remains, add to Bids book
            if remaining_qty > 0:
                entry = BidEntry(
                    neg_price=-order.price, # Invert for Max-Heap behavior
                    timestamp=order.timestamp,
                    order=order,
                    remaining_qty=remaining_qty
                )
                heapq.heappush(self.bids, entry)

        else:
            # SELL ORDER: Match against Bids (Highest Buyers)
            while remaining_qty > 0 and self.bids:
                best_bid = self.bids[0] # Peek at best offer
                best_bid_price = -best_bid.neg_price # Revert negation

                # Check Price Condition: Sell Price <= Buy Price
                if order.price <= best_bid_price:
                    # EXECUTION (Match)
                    exec_qty = min(remaining_qty, best_bid.remaining_qty)
                    exec_price = best_bid_price # Maker's price

                    trade = Trade(
                        buyer_agent_id=best_bid.order.agent_id,
                        seller_agent_id=order.agent_id,
                        asset=self.asset,
                        price=exec_price,
                        quantity=exec_qty,
                        timestamp=datetime.now()
                    )
                    trades.append(trade)

                    # Update quantities
                    remaining_qty -= exec_qty
                    best_bid.remaining_qty -= exec_qty

                    # Remove filled orders from the book
                    if best_bid.remaining_qty == 0:
                        heapq.heappop(self.bids)
                else:
                    # No overlap in price
                    break

            # RESTING: If quantity remains, add to Asks book
            if remaining_qty > 0:
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
