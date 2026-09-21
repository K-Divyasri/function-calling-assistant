"""Function-Calling Assistant - a little Streamlit chat front end for the package.

Ask a question, watch the agent decide which tool(s) to call, and read the answer.
The point of this app is the *trace*: every reply comes with an expandable panel
showing each tool the agent ran, the arguments it chose, and what came back. That
"showing its work" is the whole lesson of the project.

Run it from the repo root:

    streamlit run app.py

By default it uses the offline FakeModel - a keyword-based simulation of tool
selection. No API key, no internet, deterministic. That's what lets this app run on
a free host with nothing configured. Flip the sidebar to the real LLM (LiteLLM) and,
if a key is set in the host's Secrets, you get genuine model-driven tool choice.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# app.py lives next to the tool_agent package, but Streamlit's working directory
# isn't guaranteed, so put this folder on the path to make the import robust.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tool_agent.agent import Agent
from tool_agent.fake_model import FakeModel
from tool_agent import tools as tool_mod


# --- Make sure the database exists. The query_database tool reads data/company.db,
# --- which is git-ignored (so it isn't on a fresh host). Generate it once, cached. ---

@st.cache_resource
def ensure_database() -> str:
    """Create data/company.db on first run if it's missing. Returns its path."""
    if not tool_mod.DB_PATH.exists():
        import generate_data
        generate_data.main()
    return str(tool_mod.DB_PATH)


# --- The real-model path is optional. Import lazily so a host without litellm
# --- installed still runs the offline app fine. ---

def real_model_available() -> bool:
    """True only if litellm is importable AND some provider key is in the env."""
    try:
        from tool_agent.llm import has_api_key
    except Exception:
        return False
    return has_api_key()


# --- Page ---

st.set_page_config(page_title="Function-Calling Assistant", page_icon="🛠️")
st.title("Function-Calling Assistant")
st.write(
    "Give it a request. It decides which of four tools to call - do_math, "
    "get_weather, web_search, query_database - runs them, and answers. Expand the "
    "trace under each reply to see exactly what it did."
)

ensure_database()

# Sidebar controls.
st.sidebar.header("Settings")
brain = st.sidebar.radio(
    "Brain",
    ["Offline (fake model)", "Real LLM (LiteLLM)"],
    help="Offline = deterministic keyword rules, no key. Real = a genuine LLM chooses the tools.",
)
max_steps = st.sidebar.slider("Max steps", 1, 10, 5,
                              help="Guardrail: most reason/act rounds before the agent gives up.")
live_weather = st.sidebar.checkbox("Live weather", value=False,
                                   help="Let get_weather hit the keyless Open-Meteo API (needs requests + network).")

# Decide which brain we can actually use, and be honest about it in a caption.
use_real = brain == "Real LLM (LiteLLM)"
if use_real and not real_model_available():
    st.sidebar.caption(
        "No API key found (and litellm may not be installed). Add a key in the host's "
        "Secrets - e.g. GEMINI_API_KEY - to use the real model. Falling back to offline."
    )
    use_real = False

if use_real:
    st.sidebar.caption("Real model: an actual LLM is choosing the tools via LiteLLM.")
else:
    st.sidebar.caption(
        "Offline model: a keyword simulation of tool selection - it fakes the *choice* "
        "but runs the real tools. Deterministic and key-free. Great for seeing the loop."
    )


def build_model():
    """Return the chosen model object. Both expose the same .decide(messages)."""
    if use_real:
        from tool_agent.llm import DEFAULT_MODEL, LiteLLMModel
        return LiteLLMModel(model=DEFAULT_MODEL)
    return FakeModel()


# --- Chat ---

# Replay the conversation so far (Streamlit reruns the whole script each turn).
if "history" not in st.session_state:
    st.session_state.history = []  # list of (question, answer, steps)

for question, answer, steps in st.session_state.history:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.write(answer)
        with st.expander(f"Tool calls ({len(steps)})"):
            if not steps:
                st.caption("No tools were called - the model answered directly.")
            for i, step in enumerate(steps, 1):
                st.markdown(f"**{i}. `{step.tool}`**")
                st.json(step.arguments)
                st.code(step.result)

question = st.chat_input("Ask me something - maths, weather, a definition, or the company database")
if question:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            agent = Agent(build_model(), max_steps=max_steps, live_weather=live_weather)
            result = agent.run(question)
        st.write(result.answer)
        if result.stopped_early:
            st.warning(f"Stopped after the {max_steps}-step guardrail kicked in.")
        with st.expander(f"Tool calls ({len(result.steps)})"):
            if not result.steps:
                st.caption("No tools were called - the model answered directly.")
            for i, step in enumerate(result.steps, 1):
                st.markdown(f"**{i}. `{step.tool}`**")
                st.json(step.arguments)      # the arguments the agent chose
                st.code(step.result)         # what the tool handed back
    st.session_state.history.append((question, result.answer, result.steps))
