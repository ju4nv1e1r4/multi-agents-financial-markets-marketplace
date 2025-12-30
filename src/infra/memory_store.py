import logging
import numpy as np
import json
from redis.asyncio import Redis
from redis.commands.search.field import TextField, VectorField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

INDEX_NAME = "agent_memories"
VECTOR_DIM = 768

class MemoryStore:
    def __init__(self, redis_url: str, api_key: str):
        self.redis = Redis.from_url(redis_url, decode_responses=False)
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", 
            google_api_key=api_key
        )

    async def init_index(self):
        """Cria o índice vetorial no Redis se não existir."""
        try:
            await self.redis.ft(INDEX_NAME).info()
            logger.info("Índice de memória já existe.")
        except:
            logger.info("Criando novo índice vetorial...")
            schema = (
                TagField("agent_id"),
                TextField("content"),
                VectorField("embedding",
                    "FLAT", {
                        "TYPE": "FLOAT32",
                        "DIM": VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            definition = IndexDefinition(prefix=["mem:"], index_type=IndexType.HASH)
            await self.redis.ft(INDEX_NAME).create_index(schema, definition=definition)

    async def save_memory(self, agent_id: str, content: str):
        """Gera o embedding e salva no Redis."""
        try:
            vector = await self.embeddings.aembed_query(content)
            vector_bytes = np.array(vector, dtype=np.float32).tobytes()

            key = f"mem:{agent_id}:{hash(content)}"
            await self.redis.hset(key, mapping={
                "agent_id": agent_id,
                "content": content,
                "embedding": vector_bytes
            })
            logger.debug(f"Memória salva para {agent_id}")
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {e}")

    async def recall_memories(self, agent_id: str, context_query: str, k=3) -> str:
        """Busca as 'k' memórias mais parecidas com o contexto atual."""
        try:
            query_vector = await self.embeddings.aembed_query(context_query)
            query_bytes = np.array(query_vector, dtype=np.float32).tobytes()

            base_query = f"(@agent_id:{{{agent_id}}})=>[KNN {k} @embedding $vec AS score]"
            
            q = Query(base_query)\
                .return_fields("content")\
                .sort_by("score")\
                .dialect(2)

            results = await self.redis.ft(INDEX_NAME).search(q, query_params={"vec": query_bytes})

            if not results.docs:
                return "Nenhuma memória relevante encontrada."

            memories_text = "\n".join([f"- {doc.content}" for doc in results.docs])
            return memories_text

        except Exception as e:
            logger.error(f"Erro ao buscar memórias: {e}")
            return ""
