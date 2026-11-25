"""Servidor web: expone el grafo de LangGraph como API y sirve la página HTML.

Uso (desde la raíz del proyecto):
    python server.py
y abre http://127.0.0.1:8000

Nota Windows: no uses `uvicorn --reload`; en Windows ese modo usa un bucle de eventos
que no puede lanzar el proceso del servidor MCP.
"""
import json
import os
import re
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from pydantic import BaseModel

from app.agentes import crear_cliente_mcp
from app.config import CARPETA_CHROMA, RAIZ, falta_clave, nombre_modelo
from app.grafo import construir_grafo

CARPETA_WEB = RAIZ / "web"
recursos: dict = {"grafo": None, "error": None}


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Al arrancar: abre UNA sesión MCP (el servidor FastMCP queda vivo) y compila el grafo."""
    async with AsyncExitStack() as pila:
        try:
            if aviso := falta_clave():
                raise RuntimeError(aviso)
            if not CARPETA_CHROMA.exists():
                raise RuntimeError("No existe chroma_db/: ejecuta antes `python -m app.ingesta`")
            sesion = await pila.enter_async_context(crear_cliente_mcp().session("normas_aerolinea"))
            herramientas = await load_mcp_tools(sesion)
            recursos["grafo"] = await construir_grafo(herramientas_mcp=herramientas)
            print(f"Asistente listo en http://127.0.0.1:{os.getenv('PUERTO', '8000')}")
        except Exception as error:  # la web arranca igual y muestra el problema
            recursos["error"] = str(error)
            print(f"[AVISO] El asistente no está disponible: {error}")
        yield


app = FastAPI(title="Brisa · Asistente de Céfiro Airlines", lifespan=ciclo_de_vida)
app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")


class Turno(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str


class Peticion(BaseModel):
    mensaje: str
    historial: list[Turno] = []


@app.get("/")
async def inicio():
    return FileResponse(CARPETA_WEB / "index.html")


@app.get("/api/estado")
async def estado():
    return {"listo": recursos["grafo"] is not None, "error": recursos["error"], "modelo": nombre_modelo()}


def _fuentes(texto: str) -> list[str]:
    return sorted(set(re.findall(r"[\w\-]+\.md", texto)))


def _mensaje_error(error: Exception) -> str:
    texto = str(error)
    if "401" in texto or "invalid_api_key" in texto or "unauthorized" in texto.lower():
        return "La clave del modelo no es válida. Revisa el fichero .env y reinicia el servidor."
    if "tokens per day" in texto or "TPD" in texto:
        return ("Se ha agotado el límite DIARIO gratuito de este modelo en Groq. Se va liberando poco a "
                "poco; mientras, puedes cambiar MODELO en .env (p. ej. groq:openai/gpt-oss-20b) y reiniciar.")
    if "429" in texto or "rate limit" in texto.lower():
        return "He superado el límite gratuito de peticiones del modelo. Espera unos segundos y vuelve a intentarlo."
    return f"Ha ocurrido un error: {texto[:300]}"


@app.post("/api/chat")
async def chat(peticion: Peticion):
    """Devuelve un flujo NDJSON: una línea JSON por cada paso del grafo."""

    async def eventos():
        def linea(datos: dict) -> str:
            return json.dumps(datos, ensure_ascii=False) + "\n"

        grafo = recursos["grafo"]
        if grafo is None:
            yield linea({"tipo": "error", "texto": recursos["error"] or "El asistente no está listo."})
            return

        # Historial corto (últimos 8 turnos) para que entienda preguntas de seguimiento
        mensajes = [
            HumanMessage(t.texto) if t.rol == "usuario" else AIMessage(t.texto)
            for t in peticion.historial[-8:]
        ]
        mensajes.append(HumanMessage(peticion.mensaje))

        fuentes: set[str] = set()
        try:
            async for paso in grafo.astream({"messages": mensajes}, stream_mode="updates"):
                for nodo, cambios in paso.items():
                    if nodo == "supervisor":
                        yield linea({"tipo": "decision", "destino": cambios["siguiente"], "tarea": cambios["tarea"]})
                    elif nodo == "responder":
                        texto = cambios["messages"][-1].text
                        # Fuentes citadas en la respuesta; si no cita ninguna, las consultadas
                        citadas = _fuentes(texto) or sorted(fuentes)
                        yield linea({"tipo": "respuesta", "texto": texto, "fuentes": citadas})
                    else:
                        hallazgo = cambios["hallazgos"][-1]
                        fuentes.update(_fuentes(hallazgo))
                        texto = hallazgo.split("] ", 1)[-1]
                        yield linea({"tipo": "hallazgo", "agente": nodo, "texto": texto})
        except Exception as error:
            yield linea({"tipo": "error", "texto": _mensaje_error(error)})

    return StreamingResponse(eventos(), media_type="application/x-ndjson")


if __name__ == "__main__":
    import uvicorn

    import os

    puerto = int(os.getenv("PUERTO", "8000"))  # cámbialo en .env si el 8000 está ocupado
    uvicorn.run(app, host="127.0.0.1", port=puerto)
