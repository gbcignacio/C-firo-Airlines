"""Configuración común: rutas, modelo de lenguaje y modelo de embeddings."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.embeddings import Embeddings

# Lee las variables del fichero .env (por ejemplo, GROQ_API_KEY)
load_dotenv()
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # ChromaDB sin telemetría

RAIZ = Path(__file__).parent.parent
CARPETA_DOCS = RAIZ / "docs"          # normas de la aerolínea de las que aprende el RAG
CARPETA_CHROMA = RAIZ / "chroma_db"   # donde ChromaDB guarda la base vectorial
COLECCION = "normas_aerolinea"          # nombre de la "tabla" dentro de ChromaDB

# Modelo de embeddings multilingüe que se ejecuta en tu ordenador (gratis, sin clave)
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


# Proveedor del LLM: Ollama (Cloud o local) si hay OLLAMA_API_KEY o PROVEEDOR=ollama; si no, Groq
PROVEEDOR = os.getenv("PROVEEDOR") or ("ollama" if os.getenv("OLLAMA_API_KEY") else "groq")


def nombre_modelo() -> str:
    if PROVEEDOR == "ollama":
        return os.getenv("MODELO_OLLAMA", "qwen3:4b-instruct")
    return os.getenv("MODELO", "groq:openai/gpt-oss-120b")


def falta_clave() -> str | None:
    """Devuelve un aviso si falta la clave del proveedor elegido."""
    if PROVEEDOR == "ollama":
        local = "localhost" in os.getenv("OLLAMA_URL", "") or "127.0.0.1" in os.getenv("OLLAMA_URL", "")
        return None if os.getenv("OLLAMA_API_KEY") or local else "Falta OLLAMA_API_KEY en el fichero .env"
    return None if os.getenv("GROQ_API_KEY") else "Falta GROQ_API_KEY (u OLLAMA_API_KEY) en el fichero .env"


def crear_modelo():
    """Modelo de lenguaje (LLM).

    - Ollama Cloud (por defecto si hay OLLAMA_API_KEY): gpt-oss:120b en https://ollama.com
      Para Ollama local: OLLAMA_URL=http://localhost:11434 y sin clave.
    - Groq: openai/gpt-oss-120b en el plan gratuito.
    """
    if PROVEEDOR == "ollama":
        from langchain_ollama import ChatOllama

        clave = os.getenv("OLLAMA_API_KEY")
        url = os.getenv("OLLAMA_URL", "https://ollama.com")
        extra = {}
        if "localhost" in url or "127.0.0.1" in url:
            # En local: contexto suficiente para los fragmentos del RAG y las herramientas
            extra = {"num_ctx": 8192}
        return ChatOllama(
            model=nombre_modelo(),
            base_url=url,
            client_kwargs={"headers": {"Authorization": f"Bearer {clave}"}} if clave else {},
            temperature=0,
            **extra,
        )
    extra = {}
    if "gpt-oss" in nombre_modelo():
        # Razonamiento corto: respuestas más rápidas y menos tokens (límite gratuito de Groq)
        extra = {"reasoning_effort": "low"}
    # max_retries alto: si Groq pide esperar (límite por minuto del plan gratuito), reintenta solo
    return init_chat_model(nombre_modelo(), temperature=0, max_retries=10, **extra)


class EmbeddingsLocales(Embeddings):
    """Convierte textos en vectores con la librería fastembed.

    Hereda de la clase Embeddings de LangChain para que ChromaDB sepa usarla.
    """

    def __init__(self):
        from fastembed import TextEmbedding

        # La primera vez descarga el modelo (unos 220 MB) y lo guarda en caché
        self.modelo = TextEmbedding(MODELO_EMBEDDINGS)

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.modelo.embed(textos)]

    def embed_query(self, texto: str) -> list[float]:
        return self.embed_documents([texto])[0]


def crear_embeddings() -> Embeddings:
    return EmbeddingsLocales()
