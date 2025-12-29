# 🤖 Multi-Agent Marketplace Simulation

> **Status:** 🚧 Phase 2: Intelligence Layer (Active)

A high-fidelity simulation of an autonomous marketplace where AI Agents act as economic actors (Producers, Consumers, Speculators), creating emergent market dynamics through a centralized Limit Order Book.

Designed as a technical challenge for **CloudWalk**, focusing on system resilience, financial accuracy, and agentic behaviors.

## 🏗️ Architecture Overview

The system follows a strictly decoupled **Event-Driven Architecture** using Redis Pub/Sub to separate the Matching Engine from the Agent Minds.

### 1. The Core Engine (Market Microstructure)
Unlike simple swap mechanisms, this simulation implements a robust **Continuous Double Auction** mechanism via a Limit Order Book (LOB).
- **Algorithm:** Price-Time Priority (FIFO).
- **Data Structures:** Min/Max Heaps for O(1) access to best bid/ask.
- **Settlement:** Instantaneous atomic execution handling partial fills and resting orders.
- **Protocol:** Asynchronous processing via `market:orders` and `market:ticker` channels.

### 2. The Agents (The Brains)
Agents operate on a **Perceive-Reason-Act** loop powered by LLMs (Gemini Flash).
- **Perception:** Agents analyze the Order Book depth and their own inventory/balance.
- **Reasoning:** Each agent has a distinct Persona (e.g., *FOMO Trader*, *Conservative Market Maker*, *Distressed Producer*) that dictates their strategy.
- **Action:** Agents output strict JSON commands to place Limit or Market orders.

## 🛠️ Tech Stack

- **Language:** Python 3.11 (Heavy use of `Pydantic` for strict typing).
- **Orchestration:** LangChain / Custom Loop.
- **Database/Messaging:** Redis Stack (RedisJSON + Pub/Sub).
- **LLM:** Google Gemini Flash (Optimized for latency and throughput).
- **Infrastructure:** Docker & Docker Compose (End-to-end reproducibility).

## 🚀 How to Run

### Prerequisites
- Docker & Docker Compose installed.
- A valid `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) in a `.env` file.

### Steps
1. Clone the repository.
2. Create your `.env` file:
   ```bash
   cp .env.example .env
   # Add your API Key
3. Start the simulation:
```bash
# Starts Redis and the Market Engine
docker-compose up --build
```
4. In a separate terminal, launch the agents:
```bash
# This script instantiates the agents and connects them to the Redis bus
python src/utils/simulation.py
```

## Current Capabilities (v0.2)

[x] Real-time Order Matching: Bids and Asks are matched based on price/time priority.

[x] Emergent Behavior: Agents react to price spikes (FOMO) and liquidity crunches.

[x] Resilience: The Engine handles invalid payloads and connectivity drops without crashing.

[x] Logging: Full transaction logs available in stdout (structured logging).

Built by me