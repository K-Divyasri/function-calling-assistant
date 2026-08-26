# Deploy checklist — Function-Calling Assistant

This is the project's "definition of done." Walk it top to bottom. Don't tick a box you
haven't actually verified by running the command — "should work" isn't "works."

Everything below runs from inside `build_from_scratch/` (the repo root).

## Runs locally

- [ ] Fresh virtual environment, dependencies installed cleanly:
      `python -m venv .venv ; .\.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt`
- [ ] The database generates without error:
      `python generate_data.py` (look for `data/company.db`)
- [ ] The offline assistant answers, no key needed:
      `python -m tool_agent "weather in Paris and what is 15% of 240?"`
- [ ] The trace is visible with `--verbose`:
      `python -m tool_agent "who works in Engineering in London?" --verbose`
- [ ] `python -m tool_agent --list-tools` prints the four tools.
- [ ] (Optional) `--real` uses a genuine LLM with a key in `.env`, OR soft-fails with a hint
      without one. The offline path never needs a key.

## The web app runs

- [ ] `pip install streamlit` then `streamlit run app.py` opens the chat app.
- [ ] Asking a question shows the answer AND an expandable "Tool calls" trace.
- [ ] It works with the sidebar on **Offline (fake model)** and NO key set.

## Tests pass

- [ ] `pytest -q` from the repo root is all green — 24 tests.
- [ ] You ran it in the fresh venv, so you know the (zero) core deps are complete.
- [ ] Tests need no key and no network — they run entirely on the offline fake model.

## README is recruiter-ready

- [ ] `README.md` exists at the repo root and covers: the problem, what the assistant does,
      the four tools, how the agent loop works, how to run it, and what you learned.
- [ ] A real command block is pasted in (not paraphrased).
- [ ] A screenshot of the CLI trace or the Streamlit app is embedded.
- [ ] The CI status badge is at the top.

## Hosting requirements.txt is ready

- [ ] `streamlit>=1.30` is uncommented in `requirements.txt` (the app won't start on a host
      otherwise — the core ships with everything commented out).
- [ ] `requests>=2.28` uncommented if you want the live-weather checkbox to work on the host.
- [ ] `litellm>=1.40` + `python-dotenv>=1.0` uncommented ONLY if you're adding an API key in the
      host's Secrets for the real-model toggle. Skipping them is fine — the app defaults offline.

## Secrets are clean

- [ ] `.gitignore` contains `.env` (plus `data/company.db`, `__pycache__/`, `.venv/`).
- [ ] `git status` shows `.env` is NOT tracked.
- [ ] `git ls-files` output contains NO `.env` and NO `data/company.db` (only `.env.example`).
- [ ] No API key is hardcoded anywhere in the source.

## Pushed to GitHub

- [ ] Repo created empty on github.com (no auto README/license), named
      `function-calling-assistant`, public.
- [ ] `git init` → `git add .` → `git commit` → `git branch -M main` →
      `git remote add origin ...` → `git push -u origin main` all done.
- [ ] Files visible on the GitHub repo page after a refresh.

## Live app is up

- [ ] App deployed to Streamlit Community Cloud OR Hugging Face Spaces (Streamlit SDK).
- [ ] The public URL loads and answers a question with NO key configured (offline default).
- [ ] (Optional) `GEMINI_API_KEY` added in the host's Secrets and the real toggle works.

## CI is green

- [ ] `.github/workflows/ci.yml` is committed and pushed.
- [ ] The Actions tab shows a completed run with a green checkmark — 24 tests, no key, no network.
- [ ] If it was red, you read the log and fixed the cause, then re-ran to green.

## Repo pinned

- [ ] `function-calling-assistant` is pinned on your GitHub profile so it shows up first.

When every box is ticked, the project is done and presentable. Send the repo link and the live
app link with confidence.
