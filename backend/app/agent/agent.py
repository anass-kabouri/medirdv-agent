"""
Logique principale de l'agent conversationnel.
"""

from datetime import date

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session

from app.agent.tools import build_tools
from app.config import settings

SYSTEM_PROMPT = """Tu es l'assistant de prise de rendez-vous de MediRDV, un cabinet medical.

Regles importantes :
- Verifie TOUJOURS la disponibilite (check_availability) avant de proposer ou reserver un creneau.
- Ne invente JAMAIS un id de creneau, de praticien ou de rendez-vous : utilise toujours les outils pour les obtenir.
- Si un creneau est deja pris au moment de la reservation, propose immediatement une alternative disponible.
- Demande le nom complet et l'email du patient avant de finaliser une reservation, si tu ne les as pas deja.
- Si le patient demande a voir ses rendez-vous existants, utilise get_patient_history (demande son email si besoin).
- Si le patient veut deplacer/reprogrammer un rendez-vous, utilise reschedule_appointment
  (cherche d'abord le nouveau creneau via check_availability).
- Si le patient cherche un type de specialiste sans nommer un praticien precis, utilise le
  parametre specialty de check_availability plutot que de deviner un nom.
- Reste concis, professionnel et rassurant.
- Reponds toujours en francais.
- La date d'aujourd'hui est {today}.
"""

MAX_TOOL_ITERATIONS = 5


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts).strip()

    return str(content)


def run_agent(db: Session, history: list[dict]) -> str:
    tools = build_tools(db)
    tools_by_name = {t.name: t for t in tools}

    llm = ChatAnthropic(
        model=settings.claude_model,
        api_key=settings.anthropic_api_key,
    ).bind_tools(tools)

    messages = [SystemMessage(content=SYSTEM_PROMPT.format(today=date.today().isoformat()))]
    for turn in history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))

    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return _extract_text(response.content)

        for tool_call in response.tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            if tool is None:
                result = f"Outil inconnu : {tool_call['name']}"
            else:
                result = tool.invoke(tool_call["args"])

            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))

    return "Desole, je n'ai pas reussi a traiter ta demande. Peux-tu reformuler ?"