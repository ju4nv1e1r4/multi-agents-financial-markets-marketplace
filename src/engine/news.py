import asyncio
import json
import random
from redis.asyncio import Redis

NEWS_SCENARIOS = [
    "Uma seca severa atingiu as plantações. A produção de FOOD vai cair pela metade.",
    "Foi descoberta uma nova técnica de corte de madeira. WOOD ficará abundante.",
    "Rumores de guerra aumentam a demanda por estoques de segurança de FOOD.",
    "O governo anunciou subsídios para construção. Demanda por WOOD deve explodir.",
    "Tudo calmo no mercado. Previsão de tempo bom e colheitas estáveis.",
]

async def broadcast_news(redis: Redis):
    while True:
        await asyncio.sleep(60) 
        
        news_content = random.choice(NEWS_SCENARIOS)
        
        event = {
            "type": "NEWS",
            "content": news_content,
            "timestamp": "..."
        }

        await redis.publish("market:news", json.dumps(event))
        await redis.lpush("market:news_history", json.dumps(event))
        
        print(f"BREAKING NEWS: {news_content}")
