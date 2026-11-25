"""Orquestación con LangGraph: un supervisor reparte el trabajo entre especialistas.

INICIO -> supervisor -> (documentalista | calculadora) -> supervisor -> ...
       -> responder -> FIN
"""
import operator
from datetime import date
from typing import Annotated, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field

from app.agentes import crear_especialistas
from app.config import crear_modelo

MAX_PASOS = 4  # límite de seguridad para que el supervisor no entre en bucle
MAX_POR_AGENTE = 2  # veces que puede actuar cada especialista en una misma pregunta


class Estado(MessagesState):
    """Estado compartido del grafo. La clave "messages" ya viene de MessagesState."""

    siguiente: str  # a quién le toca actuar
    tarea: str  # encargo para ese especialista
    hallazgos: Annotated[list[str], operator.add]  # se acumulan, no se sustituyen
    necesita_calculo: bool  # lo decide el supervisor en su primera decisión


class Decision(BaseModel):
    """Respuesta estructurada del supervisor."""

    siguiente: Literal["documentalista", "calculadora", "FIN"] = Field(
        description="Quién actúa ahora, o FIN si ya hay información suficiente."
    )
    tarea: str = Field(description="Encargo completo, con todos los datos y reglas. Vacío si FIN.")
    necesita_calculo: bool = Field(
        description="True si la última pregunta pide una cantidad que hay que calcular "
        "(euros, millas, horas...); False si basta con consultar las normas."
    )


PROMPT_SUPERVISOR = """Eres el supervisor del asistente de Céfiro Airlines (aerolínea ficticia).
Hoy es {hoy}. No respondes al pasajero: decides qué especialista actúa.
- documentalista: busca en las normas de la aerolínea (tarifas y equipaje, cambios y
  cancelaciones, retrasos y reclamaciones, rutas y distancias, millas Céfiro Club, FAQ).
- calculadora: hace cuentas (coste de equipaje, compensación por retraso, reembolso al
  cancelar, coste de cambiar un vuelo, millas ganadas y horas entre dos fechas).
Atiende a la ÚLTIMA pregunta del pasajero; los mensajes anteriores son solo contexto.

Reglas:
1. Si la pregunta pide una CANTIDAD (euros, millas, horas): primero el documentalista busca
   las reglas y cifras (precios, importes, porcentajes, distancias); en cuanto las tengas,
   pasa a la calculadora con TODOS los datos del pasajero y TODAS las reglas encontradas,
   copiadas tal como las dice la normativa, sin precalcular nada.
2. Si el documentalista ya ha dado las reglas, el siguiente paso es la calculadora (si hay
   que calcular algo) o FIN; no lo vuelvas a llamar salvo que falte un dato concreto.
   En cuanto la calculadora dé un resultado, responde FIN.
3. Pide al documentalista TODO lo que haga falta en un solo encargo (por ejemplo, la
   distancia de la ruta Y los importes de compensación).
4. Si la pregunta no pide ninguna cuenta (por ejemplo, qué documentación necesito o si
   algo está permitido), basta con el documentalista: después responde FIN.

Ejemplo: «Mi vuelo Madrid–Nueva York llegó con 5 horas de retraso, ¿cuánto me pagan?» →
documentalista (distancia Madrid–Nueva York y tabla de compensaciones por retraso) →
calculadora (compensacion_retraso con esa distancia, las horas y los importes) → FIN.

Información recogida hasta ahora:
{hallazgos}

Si ya hay información suficiente, o la pregunta no tiene que ver con la aerolínea (por ejemplo, un saludo), responde FIN."""

PROMPT_RESPUESTA = """Eres Brisa, la asistente virtual de Céfiro Airlines, una aerolínea ficticia. Hablas
de tú, con tono cercano y profesional, en español.
Responde al pasajero con claridad usando SOLO esta información y cita entre paréntesis
el fichero de la fuente (por ejemplo, (tarifas_y_equipaje.md)):
{hallazgos}

Usa Markdown ligero: **negritas** para las cifras clave y listas cortas si ayudan.
Ve directo a la respuesta: NO saludes ni te presentes, salvo que el mensaje sea solo un
saludo o algo ajeno a la aerolínea (entonces preséntate brevemente y di en qué puedes ayudar).
NO hagas cuentas tú: si la calculadora ha dado un resultado, ese es el dato final; dalo
con claridad y resume en una lista corta los datos que se han usado.
Si no hay información suficiente, dilo y sugiere escribir a ayuda@cefiro-airlines.example."""


def _texto(estado: Estado) -> str:
    return "\n".join(estado.get("hallazgos", [])) or "Ninguna todavía."


async def construir_grafo(modelo=None, herramientas_mcp=None):
    modelo = modelo or crear_modelo()
    especialistas = await crear_especialistas(modelo, herramientas_mcp)
    decisor = modelo.with_structured_output(Decision)  # responde con el esquema Decision

    # --- Nodos: reciben el estado y devuelven solo lo que cambian ---
    def _veces(estado: Estado, nombre: str) -> int:
        return sum(h.startswith(f"[{nombre}]") for h in estado.get("hallazgos", []))

    def _terminar(estado: Estado, necesita_calculo: bool) -> dict:
        """Antes de ir a FIN: si hacía falta calcular y la calculadora no ha actuado, le toca a ella."""
        if necesita_calculo and _veces(estado, "calculadora") == 0:
            pregunta = estado["messages"][-1].text
            tarea = (f"Pregunta del pasajero: {pregunta}\nReglas y cifras de la normativa:\n"
                     f"{_texto(estado)}\nCalcula el resultado con tus herramientas.")
            return {"siguiente": "calculadora", "tarea": tarea, "necesita_calculo": necesita_calculo}
        return {"siguiente": "FIN", "tarea": "", "necesita_calculo": necesita_calculo}

    async def supervisor(estado: Estado) -> dict:
        necesita = estado.get("necesita_calculo", False)
        hallazgos = estado.get("hallazgos", [])
        # Si la calculadora acaba de dar un resultado, ese es el dato final: a responder
        # (ahorra una llamada al modelo y evita que repita la cuenta)
        if hallazgos and hallazgos[-1].startswith("[calculadora]") and "No he podido" not in hallazgos[-1]:
            return {"siguiente": "FIN", "tarea": "", "necesita_calculo": necesita}
        if len(hallazgos) >= MAX_PASOS:
            return _terminar(estado, necesita)
        prompt = PROMPT_SUPERVISOR.format(hoy=date.today().isoformat(), hallazgos=_texto(estado))
        decision = await decisor.ainvoke([SystemMessage(prompt), *estado["messages"]])
        if not estado.get("hallazgos"):  # la primera decisión fija si hay que calcular
            necesita = decision.necesita_calculo
        # Salvaguardas: cada especialista actúa como mucho MAX_POR_AGENTE veces,
        # y no se termina sin la calculadora si la pregunta pedía una cuenta
        if decision.siguiente == "FIN" or _veces(estado, decision.siguiente) >= MAX_POR_AGENTE:
            return _terminar(estado, necesita)
        return {"siguiente": decision.siguiente, "tarea": decision.tarea, "necesita_calculo": necesita}

    def crear_nodo(nombre: str):
        async def nodo(estado: Estado) -> dict:
            # El especialista solo recibe su encargo, no toda la conversación
            entrada = {"messages": [HumanMessage(estado["tarea"])]}
            try:
                resultado = await especialistas[nombre].ainvoke(entrada)
                texto = resultado["messages"][-1].text
            except Exception as error:
                if "429" in str(error):  # límite de peticiones: que lo gestione la web
                    raise
                # Un fallo de una herramienta no tumba el grafo: el supervisor lo ve y decide
                texto = f"No he podido completar el encargo ({type(error).__name__}: {error})."
            return {"hallazgos": [f"[{nombre}] {texto}"]}

        return nodo

    async def responder(estado: Estado) -> dict:
        prompt = PROMPT_RESPUESTA.format(hallazgos=_texto(estado))
        respuesta = await modelo.ainvoke([SystemMessage(prompt), *estado["messages"]])
        return {"messages": [respuesta]}

    # --- Grafo: nodos y aristas ---
    grafo = StateGraph(Estado)
    grafo.add_node("supervisor", supervisor)
    grafo.add_node("responder", responder)
    for nombre in especialistas:
        grafo.add_node(nombre, crear_nodo(nombre))
        grafo.add_edge(nombre, "supervisor")  # cada especialista vuelve al supervisor

    grafo.add_edge(START, "supervisor")
    # Arista condicional: el destino depende de estado["siguiente"]
    rutas = {"documentalista": "documentalista", "calculadora": "calculadora", "FIN": "responder"}
    grafo.add_conditional_edges("supervisor", lambda estado: estado["siguiente"], rutas)
    grafo.add_edge("responder", END)
    return grafo.compile()
