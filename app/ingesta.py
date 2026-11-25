"""Ingesta: lee los documentos de la aerolínea, los trocea y los guarda en ChromaDB.

Se ejecuta una vez, y otra cada vez que cambien los documentos:
    python -m app.ingesta
"""
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from app.config import CARPETA_CHROMA, CARPETA_DOCS, COLECCION, crear_embeddings


def cargar_documentos() -> list[Document]:
    """Lee cada .md de docs/ como un Document (texto + metadatos)."""
    documentos = []
    for fichero in sorted(CARPETA_DOCS.glob("*.md")):
        texto = fichero.read_text(encoding="utf-8")
        documentos.append(Document(page_content=texto, metadata={"fuente": fichero.name}))
    return documentos


def trocear(documentos: list[Document]) -> list[Document]:
    """Parte los documentos en fragmentos (chunks).

    1. Por apartados de Markdown (##), para que cada fragmento sea de un solo tema.
    2. Si un apartado es largo, en trozos de ~500 caracteres con 50 de solape.
    3. Cada trozo empieza por el título de SU apartado (y no por el título del
       documento, que mezclaría temas y empeoraría la búsqueda).
    """
    por_apartados = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "documento"), ("##", "apartado")], strip_headers=True
    )
    troceador = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    fragmentos = []
    for doc in documentos:
        for apartado in por_apartados.split_text(doc.page_content):
            titulo = apartado.metadata.get("apartado", "")
            if not titulo:  # texto antes del primer ##: solo el título del documento
                continue
            metadatos = {"fuente": doc.metadata["fuente"], "apartado": titulo}
            for trozo in troceador.split_text(apartado.page_content):
                fragmentos.append(Document(page_content=f"{titulo}\n{trozo}", metadata=metadatos))
    return fragmentos


def indexar(embeddings=None) -> int:
    """Calcula el vector de cada fragmento y lo guarda en ChromaDB."""
    fragmentos = trocear(cargar_documentos())
    base = Chroma(
        collection_name=COLECCION,
        embedding_function=embeddings or crear_embeddings(),
        persist_directory=str(CARPETA_CHROMA),  # se guarda en disco
    )
    base.reset_collection()  # vaciamos la colección: así no quedan restos de documentos borrados
    ids = [f"{f.metadata['fuente']}-{i}" for i, f in enumerate(fragmentos)]
    base.add_documents(fragmentos, ids=ids)
    return len(fragmentos)


if __name__ == "__main__":
    total = indexar()
    print(f"Guardados {total} fragmentos en {CARPETA_CHROMA}")
