import streamlit as st
import redis
import json
import time
import pandas as pd
import random
import os
from datetime import datetime
import uuid

st.set_page_config(layout="wide", page_title="Multi-Agent Marketplace Simulation")

@st.cache_resource
def get_redis():
    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

r = get_redis()

st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
    .stMetric [data-testid="stMetricValue"] { color: black !important; }
    .stMetric [data-testid="stMetricLabel"] { color: black !important; }
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🎮 Controle")
status = r.get("system:status") or "PAUSED"

if status == "RUNNING":
    st.sidebar.success("🟢 Sistema RODANDO")
    if st.sidebar.button("PAUSAR Simulação"):
        r.set("system:status", "PAUSED")
        st.rerun()
else:
    st.sidebar.warning("🔴 Sistema PAUSADO")
    if st.sidebar.button("INICIAR Simulação"):
        r.set("system:status", "RUNNING")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("📝 Boleta Rápida")
with st.sidebar.form("order_form"):
    asset = st.selectbox("Ativo", ["WOOD", "FOOD", "GOLD", "DOLAR"])
    side = st.selectbox("Lado", ["BID", "ASK"])
    price = st.number_input("Preço", min_value=0.1, value=10.0, step=0.5)
    qty = st.number_input("Qtd", min_value=1, value=10, step=1)

    submitted = st.form_submit_button("Enviar Ordem")
    if submitted:
        order = {
            "id": str(uuid.uuid4()),
            "agent_id": "HUMAN_TRADER",
            "asset": asset,
            "side": side,
            "type": "LIMIT",
            "price": price,
            "quantity": qty,
            "timestamp": datetime.now().isoformat()
        }
        r.publish("market:orders", json.dumps(order))
        st.sidebar.success(f"Ordem enviada: {side} {qty} {asset} @ {price}")

st.sidebar.markdown("---")
if st.sidebar.button("🔥 INJETAR NOTÍCIA (CAOS)"):
    chaos = [
        "ALERTA: Praga de gafanhotos devasta 40% da safra no hemisfério sul; FOOD deve dobrar de preço.",
        "BREAKING: Incêndios incontroláveis no Canadá reduzem oferta global de WOOD em 25%.",
        "URGENTE: Embargo comercial repentino trava exportações de FOOD da maior potência agrícola.",
        "MERCADO: Boom imobiliário na Ásia esgota estoques de WOOD; construtoras em pânico.",
        "FLASH: Inundação recorde destrói armazéns principais; escassez imediata de FOOD.",
        "URGENTE: Nova tecnologia de clonagem de árvores promete triplicar oferta de WOOD em 2 anos; futuros despencam.",
        "CRISE: Greve geral de caminhoneiros paralisa distribuição de FOOD e WOOD no continente.",
        "ALERTA: Fungo resistente ataca plantações de trigo; analistas preveem colapso na oferta de FOOD.",
        "BULL MARKET: Incentivos fiscais para casas de madeira aquecem demanda por WOOD vertiginosamente.",
        "BREAKING: Super safra inesperada inunda o mercado de FOOD; preços caem ao menor nível em uma década.",
        "URGENTE: Regulamentação ambiental proíbe corte em florestas certificadas; choque de oferta em WOOD.",
        "MERCADO: Seca severa esvazia hidrovias e impede transporte de FOOD para portos exportadores.",
        "FLASH: Descoberta de cupim mutante em reservas estratégicas de WOOD; qualidade comprometida.",
        "ALERTA: Gigante do agronegócio declara falência; incerteza domina mercado futuro de FOOD.",
        "URGENTE: Tarifa de importação sobre WOOD é zerada; mercado local teme invasão de produto estrangeiro.",
        "BREAKING: Onda de calor histórica queima lavouras antes da colheita; futuros de FOOD em limite de alta.",
        "CRISE: Escândalo de contaminação em grandes lotes de FOOD gera recall massivo e desconfiança."
    ]

    randomized_chaos = random.SystemRandom(chaos)
    chaos_message = randomized_chaos.sample(chaos, len(chaos))
    news = {
        "type": "NEWS",
        "content": chaos_message[0],
        "timestamp": datetime.now().isoformat()
    }
    r.publish("market:news", json.dumps(news))
    r.lpush("market:news_history", json.dumps(news))
    st.toast("Notícia de Crise Enviada!", icon="🔥")

st.title("🚀🤖 Multi-Agent Marketplace Simulation 🤖🚀")

placeholder = st.empty()

while True:
    with placeholder.container():
        col1, col2, col3 = st.columns(3)

        p_wood = float(r.get("market:price:WOOD") or 0)
        p_food = float(r.get("market:price:FOOD") or 0)
        p_gold = float(r.get("market:price:GOLD") or 0)
        p_dolar = float(r.get("market:price:DOLAR") or 0)

        col1.metric("🌲 WOOD Price", f"${p_wood:.2f}", border=True)
        col2.metric("🍎 FOOD Price", f"${p_food:.2f}", border=True)
        col3.metric("💰 GOLD Price", f"${p_gold:.2f}", border=True)
        col1.metric("💵 Dolar Price", f"${p_dolar:.2f}", border=True)

        st.subheader("📰 News Feed")
        latest_news = r.lrange("market:news_history", 0, 0)
        if latest_news:
            news_data = json.loads(latest_news[0])
            st.info(f"**{news_data['timestamp'][11:19]}**: {news_data['content']}")
        else:
            st.caption("Sem notícias recentes.")

        st.subheader("🧠 Agent Live Feed")
        logs_raw = r.lrange("agent:logs", 0, 9)
        
        if logs_raw:
            logs_data = [json.loads(log) for log in logs_raw]
            df_logs = pd.DataFrame(logs_data)
            st.dataframe(
                df_logs, 
                column_config={
                    "timestamp": "Hora",
                    "agent_id": "Agente",
                    "action": "Ação",
                    "reasoning": "Pensamento (RAG)"
                },
                hide_index=True,
                width="stretch"
            )
        else:
            st.write("Aguardando atividade dos agentes...")

    time.sleep(1)
