"""Agentes especialistas.

Agente = modelo + instrucciones (system prompt) + herramientas.
create_agent monta el bucle: pensar -> usar herramienta -> leer resultado -> responder.
"""
import sys
from datetime import date

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import RAIZ
from app.herramientas import HERRAMIENTAS_CALCULO


def crear_cliente_mcp() -> MultiServerMCPClient:
    """Cliente MCP que sabe arrancar nuestro servidor FastMCP como proceso (stdio)."""
    return MultiServerMCPClient(
        {
            "normas_aerolinea": {
                "transport": "stdio",
                "command": sys.executable,  # el mismo Python que ejecuta este programa
                "args": ["-m", "app.servidor_mcp"],
                "cwd": str(RAIZ),
            }
        }
    )


async def cargar_herramientas_mcp() -> list:
    """Arranca el servidor MCP y convierte sus herramientas al formato LangChain."""
    return await crear_cliente_mcp().get_tools()


async def crear_especialistas(modelo, herramientas_mcp=None) -> dict:
    """Devuelve un diccionario {nombre: agente}."""
    if herramientas_mcp is None:
        herramientas_mcp = await cargar_herramientas_mcp()

    documentalista = create_agent(
        modelo,
        tools=herramientas_mcp,  # buscar_normas, que llega desde el servidor MCP
        system_prompt="Eres el documentalista de Céfiro Airlines, una aerolínea ficticia. "
        "Busca SIEMPRE con tu herramienta (puedes hacer varias búsquedas) y responde solo con lo "
        "que digan los documentos, copiando las cifras exactas y citando el fichero de la fuente. "
        "Si no está en los documentos, dilo claramente. Sé breve: como mucho 8 líneas, "
        "sin tablas, solo los datos que te piden. NUNCA hagas cuentas ni apliques las reglas "
        "al caso concreto: eso lo hace la calculadora. Tú solo das las reglas y cifras.",
        name="documentalista",
    )
    calculadora = create_agent(
        modelo,
        tools=HERRAMIENTAS_CALCULO,
        system_prompt=f"Eres la calculadora de Céfiro Airlines (equipaje, compensaciones por "
        f"retraso, reembolsos, cambios de vuelo, millas y horas entre fechas). Hoy es "
        f"{date.today():%Y-%m-%d}. Haz las cuentas SIEMPRE con tus herramientas, usando los datos "
        "y las reglas que te den en el encargo, y explica el resultado en una o dos frases. "
        "NUNCA rehagas ni corrijas las cuentas a mano: da el resultado de la herramienta tal cual. "
        "Recuerda: un viaje de ida y vuelta son 2 trayectos.",
        name="calculadora",
    )
    return {"documentalista": documentalista, "calculadora": calculadora}
