"""Servidor MCP hecho con FastMCP: ofrece la búsqueda en las normas de la aerolínea como herramienta.

Lo puede usar cualquier cliente MCP: nuestro agente, Claude Code, Claude Desktop...
Normalmente lo arranca el cliente; para lanzarlo a mano:
    python -m app.servidor_mcp
"""
from fastmcp import FastMCP
from langchain_chroma import Chroma

from app.config import CARPETA_CHROMA, COLECCION, crear_embeddings

servidor = FastMCP("normas_aerolinea")

# Abrimos la base vectorial que creó la ingesta (no la volvemos a crear)
base = Chroma(
    collection_name=COLECCION,
    embedding_function=crear_embeddings(),
    persist_directory=str(CARPETA_CHROMA),
)


@servidor.tool
def buscar_normas(consulta: str, k: int = 4) -> str:
    """Busca en las normas de Céfiro Airlines: tarifas y equipaje, cambios y cancelaciones,
    retrasos y reclamaciones, rutas y distancias, programa de millas Céfiro Club y
    preguntas frecuentes (check-in, embarque, documentación...).
    Devuelve los k fragmentos más parecidos a la consulta, con su fuente."""
    resultados = base.similarity_search(consulta, k=k)
    if not resultados:
        return "No se ha encontrado nada. ¿Se ha ejecutado la ingesta (python -m app.ingesta)?"
    return "\n\n".join(
        f"[Fuente: {doc.metadata['fuente']} · {doc.metadata.get('apartado', '')}]\n{doc.page_content}"
        for doc in resultados
    )


if __name__ == "__main__":
    # stdio: el cliente habla con el servidor por la entrada y salida estándar
    servidor.run(transport="stdio", show_banner=False, log_level="WARNING")
