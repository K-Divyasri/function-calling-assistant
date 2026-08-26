"""Tests for the agent loop and the offline router — the core behaviour."""

from __future__ import annotations

from tool_agent.agent import Agent
from tool_agent.fake_model import FakeModel


def test_agent_answers_math(agent):
    result = agent.run("what is 15% of 240?")
    assert "36" in result.answer
    assert [s.tool for s in result.steps] == ["do_math"]


def test_agent_calls_multiple_tools_in_one_turn(agent):
    # The headline capability: one request, two tools.
    result = agent.run("weather in Paris and what is 2 + 2?")
    tools_used = {s.tool for s in result.steps}
    assert tools_used == {"get_weather", "do_math"}
    assert "Paris" in result.answer and "4" in result.answer


def test_agent_uses_database_for_employee_question(agent):
    result = agent.run("who works in Engineering?")
    assert result.steps and result.steps[0].tool == "query_database"
    assert "Ada Lovelace" in result.answer


def test_agent_falls_back_to_search_for_facts(agent):
    result = agent.run("what is a transformer?")
    assert result.steps and result.steps[0].tool == "web_search"


def test_agent_plain_answer_when_no_tool_matches(agent):
    result = agent.run("hello there")
    assert result.steps == []           # no tool was called
    assert "maths" in result.answer     # the friendly capabilities message


def test_agent_records_a_trace(agent):
    result = agent.run("what is 5 * 5?")
    assert len(result.steps) == 1
    step = result.steps[0]
    assert step.tool == "do_math"
    assert "25" in step.result


def test_agent_history_has_tool_call_and_result_messages(agent):
    # The message history must contain an assistant tool_calls turn followed by a
    # tool result — the exact shape a real provider round-trip produces.
    result = agent.run("what is 1 + 1?")
    roles = [m["role"] for m in result.messages]
    assert "tool" in roles
    assistant_with_calls = [m for m in result.messages
                            if m["role"] == "assistant" and m.get("tool_calls")]
    assert assistant_with_calls


class _NeverStops:
    """A broken 'model' that always asks for a tool and never answers."""

    def decide(self, messages):
        from tool_agent.fake_model import Decision, ToolCall
        return Decision(tool_calls=[ToolCall("call_x", "do_math", {"expression": "1+1"})])


def test_max_steps_guard_stops_a_runaway_loop():
    agent = Agent(_NeverStops(), max_steps=3)
    result = agent.run("loop forever")
    assert result.stopped_early
    assert len(result.steps) == 3      # exactly max_steps rounds, then it bailed


def test_unknown_tool_name_does_not_crash():
    from tool_agent.fake_model import Decision, ToolCall

    class _AsksUnknown:
        def __init__(self):
            self.done = False

        def decide(self, messages):
            if self.done:
                return Decision(content="done")
            self.done = True
            return Decision(tool_calls=[ToolCall("call_1", "teleport", {})])

    agent = Agent(_AsksUnknown())
    result = agent.run("beam me up")
    # The bad tool produced an error string, and the loop kept going to an answer.
    assert result.steps[0].result.startswith("Error: no tool named")
    assert result.answer == "done"
