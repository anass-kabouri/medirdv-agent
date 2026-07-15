from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from app.agent import agent as agent_module


def test_run_agent_executes_tool_and_returns_final_reply(db_session, practitioner):
    first_response = AIMessage(
        content="",
        tool_calls=[{"name": "list_practitioners", "args": {}, "id": "call_1"}],
    )
    final_response = AIMessage(content="Voici les praticiens disponibles.")

    fake_llm = MagicMock()
    fake_llm.invoke.side_effect = [first_response, final_response]

    fake_chat_anthropic = MagicMock()
    fake_chat_anthropic.bind_tools.return_value = fake_llm

    with patch.object(agent_module, "ChatAnthropic", return_value=fake_chat_anthropic):
        reply = agent_module.run_agent(
            db_session, [{"role": "user", "content": "Quels praticiens sont disponibles ?"}]
        )

    assert reply == "Voici les praticiens disponibles."
    assert fake_llm.invoke.call_count == 2


def test_run_agent_returns_text_directly_without_tool_call(db_session):
    direct_response = AIMessage(content="Bonjour, comment puis-je vous aider ?")

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = direct_response

    fake_chat_anthropic = MagicMock()
    fake_chat_anthropic.bind_tools.return_value = fake_llm

    with patch.object(agent_module, "ChatAnthropic", return_value=fake_chat_anthropic):
        reply = agent_module.run_agent(db_session, [{"role": "user", "content": "Bonjour"}])

    assert reply == "Bonjour, comment puis-je vous aider ?"
    assert fake_llm.invoke.call_count == 1


def test_run_agent_stops_after_max_iterations(db_session):
    looping_response = AIMessage(
        content="",
        tool_calls=[{"name": "list_practitioners", "args": {}, "id": "call_x"}],
    )

    fake_llm = MagicMock()
    fake_llm.invoke.return_value = looping_response

    fake_chat_anthropic = MagicMock()
    fake_chat_anthropic.bind_tools.return_value = fake_llm

    with patch.object(agent_module, "ChatAnthropic", return_value=fake_chat_anthropic):
        reply = agent_module.run_agent(db_session, [{"role": "user", "content": "test"}])

    assert fake_llm.invoke.call_count == agent_module.MAX_TOOL_ITERATIONS
    assert "reformuler" in reply.lower()


def test_run_agent_handles_unknown_tool_gracefully(db_session):
    unknown_tool_response = AIMessage(
        content="",
        tool_calls=[{"name": "outil_qui_nexiste_pas", "args": {}, "id": "call_y"}],
    )
    final_response = AIMessage(content="Desole, une erreur est survenue.")

    fake_llm = MagicMock()
    fake_llm.invoke.side_effect = [unknown_tool_response, final_response]

    fake_chat_anthropic = MagicMock()
    fake_chat_anthropic.bind_tools.return_value = fake_llm

    with patch.object(agent_module, "ChatAnthropic", return_value=fake_chat_anthropic):
        reply = agent_module.run_agent(db_session, [{"role": "user", "content": "test"}])

    assert reply == "Desole, une erreur est survenue."