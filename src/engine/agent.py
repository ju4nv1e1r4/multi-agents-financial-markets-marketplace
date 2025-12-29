from src.data.models import AgentState, Order, OrderSide, AssetType, Trade

class Agent:
    def __init__(self, agent_id: str, role: str, personality: str, initial_gold: float = 1000.0):
        self.state = AgentState(
            agent_id=agent_id,
            role=role,
            inventory={asset: 0 for asset in AssetType},
            gold_balance=initial_gold,
            personality=personality
        )

    def create_order(self, asset: AssetType, side: OrderSide, price: float, quantity: int) -> Order:
        """
        Cria uma intenção de ordem.
        """
        # NOTE: A validação de saldo/estoque pode ser feita aqui ou na Exchange antes de aceitar.
        return Order(
            agent_id=self.state.agent_id,
            asset=asset,
            side=side,
            price=price,
            quantity=quantity
        )

    def update_on_trade(self, trade: Trade):
        """
        Atualiza o saldo de Ouro e Inventário do agente após um trade.
        """
        total_value = trade.price * trade.quantity

        if trade.buyer_agent_id == self.state.agent_id:
            self.state.gold_balance -= total_value
            self.state.inventory[trade.asset] += trade.quantity
        elif trade.seller_agent_id == self.state.agent_id:
            self.state.gold_balance += total_value
            self.state.inventory[trade.asset] -= trade.quantity

    def __repr__(self):
        return f"<Agent {self.state.agent_id} | Gold: ${self.state.gold_balance:.2f} | Inv: {self.state.inventory}>"
