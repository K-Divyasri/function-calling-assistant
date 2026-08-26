# Function-Calling Assistant

An assistant that decides which tool to call to answer you. Ask it a question and it
picks from four tools (a calculator, a weather lookup, a web search, and a company
database query), runs the ones it needs, and turns the results into an answer. The
whole thing runs offline with no API key by default; add a key and one flag to swap in
a real LLM doing the same job.

**Problem:** A language model on its own can't do arithmetic reliably, doesn't know
today's weather, and can't read your database. "Function calling" (a.k.a. tools) fixes
that: you hand the model a menu of functions, it decides which to call and with what
arguments, your code runs them, and the model answers from the results. This project
builds that loop, reason → act → observe, from scratch, so you can *see* it work.

**Skills demonstrated:** the agent loop (tool selection → dispatch → feed results back),
JSON tool schemas (OpenAI format), safe tool design (an `ast`-based calculator instead of
`eval`, a parameterised read-only SQL query with no injection surface), guardrails against
runaway loops, a provider-agnostic LLM call via LiteLLM, CLI design with argparse, and
pytest.

**Tech stack:** Python 3.10+ and the standard library, that's the entire core. Optional
extras: LiteLLM + python-dotenv for the real model (`--real`), `requests` for live weather
(`--live-weather`), and Streamlit for the web app.

## What it does

```powershell
python -m tool_agent "what is 15% of 240?"                       # offline, no key
python -m tool_agent "weather in Paris and what is 15% of 240?"  # calls TWO tools in one turn
python -m tool_agent "who works in Engineering in London?"       # queries the company DB
python -m tool_agent "what is RAG?"                              # web_search over a local corpus
python -m tool_agent "weather in Berlin" --verbose               # print each tool call live
python -m tool_agent "weather in Tokyo" --live-weather           # real, keyless Open-Meteo call
python -m tool_agent "weather in Berlin" --real                  # use a genuine LLM (needs a key)
python -m tool_agent "weather in Berlin" --real --model claude-sonnet-5
python -m tool_agent "..." --max-steps 3                         # tighten the runaway guardrail
python -m tool_agent --list-tools                                # show the four tools and exit
```

Run `python -m tool_agent --help` to see every flag. With no `--real`, everything runs on
the offline fake model: no key, no network, same answer every time.

The four tools:

- **do_math**: a *safe* calculator. It parses the expression with Python's `ast` and only
  allows arithmetic (`+ - * / // % **` and parentheses). It never calls `eval`, so the model
  can't smuggle code through it. `"(3 + 4) * 5 - 2"` → `"(3 + 4) * 5 - 2 = 33"`.
- **get_weather**: a canned offline table for eight cities (Paris → "clear, 15C"). With
  `--live-weather` it calls Open-Meteo (free, no key) and falls back to the table on any error.
- **web_search**: keyword search over a tiny 8-document local corpus (python, RAG, embeddings,
  agents, ...). The real-world version would be an API like Tavily; this keeps it offline.
- **query_database**: a read-only, *parameterised* lookup over a bundled SQLite database
  (15 employees, 10 products). The model picks a table and optional filters, never raw SQL,
  so there's no injection surface.

## How it works

The package is split so each file does one job, which is also what makes it testable:

```
tool_agent/
├── tools.py        the four real tools (do_math, get_weather, web_search, query_database)
├── schemas.py      the JSON tool schemas the model reads + dispatch_tool (name -> function)
├── fake_model.py   a deterministic offline "model" that picks tools by keyword, no key, no net
├── llm.py          the real model path via LiteLLM (Gemini/Claude/OpenAI), genuine tool calls
├── agent.py        the agent loop: ask -> maybe call tools -> feed results back -> repeat
├── cli.py          the argparse command-line front door
└── __main__.py     makes `python -m tool_agent` work
```

The key idea is that `agent.py` doesn't care what's choosing the tools. It takes any object
with a `.decide(messages) -> Decision` method, so the *identical* loop drives both the offline
`FakeModel` and the real `LiteLLMModel`, swapping the brain is a one-line change. The loop:

1. Send the conversation to the model. It replies either with a final text answer, or with a
   request to call one or more tools (each a name + JSON arguments).
2. If it's an answer, stop. If it's tool calls, run each one via `dispatch_tool`, append the
   results to the conversation as `role: "tool"` messages, and loop.
3. A guardrail stops after `max_steps` rounds and sets `stopped_early=True`, so a model that
   keeps asking for tools without ever answering can't loop forever.

`dispatch_tool` is deliberately defensive: an unknown tool name, invalid JSON arguments, or a
hallucinated extra argument all come back as a friendly `"Error: ..."` string instead of a
crash: one bad tool call should never take down the whole run.

**Offline-first by design.** The default path uses `FakeModel`, a pile of regex rules that
*simulates* tool selection. It's honest about being a simulation, it fakes the model's *choice*
but runs the genuine tools, and it's what lets the tests, the notebooks, and the hosted web app
run with zero setup. Turn on `--real` to see an actual LLM make the same decisions.

## Run locally

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt   # core needs nothing; this installs the optional extras
python generate_data.py           # writes data/company.db (git-ignored, deterministic)
python -m tool_agent "weather in Paris and who works in Engineering in London?"
pytest -q                         # 24 tests
```

The core assistant has **zero** runtime dependencies; `requirements.txt` only lists optional
upgrades (LiteLLM, requests, Streamlit), each commented so you enable what you want. The tests
run entirely on the offline fake model, so `pytest` needs no key and no network.

Optional `--real` flag: copy `.env.example` to `.env`, add a free Gemini key from
https://aistudio.google.com/apikey, then:

```powershell
python -m tool_agent "weather in Berlin and what is 12% of 90?" --real --verbose
```

Without a key, `--real` prints a short setup hint and the offline path keeps working fine.

There's also a Streamlit chat app (`app.py`) that shows the tool-call trace visually:

```powershell
pip install streamlit
streamlit run app.py
```

## What I learned

- The agent loop is smaller than it sounds: reason → act → observe, in a `for` loop with a step
  limit. Everything fancier (ReAct, multi-agent) is a variation on it.
- Why tool *descriptions* are the real interface: the model decides *when* to call a tool almost
  entirely from the words in its JSON schema.
- How to make tools safe to hand a model: parse arithmetic with `ast` instead of `eval`, and pass
  the model column filters rather than raw SQL so there's nothing to inject.
- Why a guardrail on step count matters, and how to make one bad tool call return an error string
  the model can read instead of crashing the loop.
- How LiteLLM lets the same OpenAI-shaped tool-calling code target Gemini, Claude, or OpenAI by
  changing one string.
