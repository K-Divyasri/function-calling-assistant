# Publishing the Function-Calling Assistant

This project has two shippable things, and "hosting" covers both.

The first is the **GitHub repo** — the polished `build_from_scratch/` folder, with a clean
README and a green CI checkmark that proves the tests pass on every push. That's the part a
recruiter opens.

The second is the **Streamlit chat app** — `app.py`. Unlike a CLI, a web app *is* something
you can deploy to a live URL that anyone can click. You ask it a question in a chat box, and
it shows you which tools the agent called and what they returned. Putting that on the internet,
free, with a link you can share, is a genuinely strong portfolio piece.

The one thing that makes deploying this app painless: **it defaults to the offline fake model**,
so it runs on a free host with *no API key and no configuration at all*. The "use the real LLM"
toggle only lights up if a key is present in the host's Secrets. That means you can deploy first
and worry about keys never, or later.

Everything below assumes you're working from inside `build_from_scratch/` — that folder is the
repo root.

---

## Step 0 — Install Git and make a GitHub account

Git tracks versions of your files on your laptop. GitHub is the website that stores a copy
online so other people (and recruiters) can see it. You need both — they're different things.

### Install Git

1. Go to https://git-scm.com/download/win. The download starts on its own.
2. Run the installer. Click Next through every screen — the defaults are fine.
3. Open a **new** PowerShell window (new, so it picks up the install) and check it worked:

```powershell
git --version
```

If you see something like `git version 2.45.0`, you're set. If PowerShell doesn't recognize
`git`, close every terminal, open a fresh one, and try again.

### Make a GitHub account

1. Go to https://github.com and sign up. Use your real email (`mathuransada@gmail.com` is the
   one on file). Verify it.
2. Pick a username you'd be happy putting on a CV — recruiters see it.

### Tell Git who you are

Do this once per machine. Use the same email as your GitHub account.

```powershell
git config --global user.name "Your Name"
git config --global user.email "mathuransada@gmail.com"
```

---

## Step 1 — Know what goes in the repo and what must NOT

Some files belong on GitHub; some must never leave your laptop. The line between them is a
file called `.gitignore` — a plain-text list of things Git pretends don't exist. The project
ships one at the repo root. Open `build_from_scratch/.gitignore` and confirm it has at least:

```
.env
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.pytest_cache/
data/company.db
```

What each one keeps out and why:

- **`.env`** — the important one. If you turn on the real model, your `.env` holds an API key,
  and a key is a password. If you commit it, it's on the public internet **forever** (Git keeps
  the whole history), and bots scrape GitHub for leaked keys within minutes. So: **`.env` never
  gets committed, ever.** The repo ships a `.env.example` instead — variable names with blank
  values, safe to commit — so other people know what to fill in.
- **`data/company.db`** — the SQLite database the `query_database` tool reads. It's *generated*,
  not source: `python generate_data.py` rebuilds it identically every time (it's deterministic).
  There's no reason to store generated output in Git, and the app regenerates it on first run
  anyway. Keep it ignored.
- **`__pycache__/`, `*.pyc`, `.pytest_cache/`, `*.egg-info/`** — junk Python and pytest create
  as they run. Nobody needs to see it.
- **`.venv/`, `venv/`** — your virtual environment, hundreds of megabytes specific to your
  machine. Other people rebuild it from `requirements.txt`.

Rule of thumb: **source code, config, and docs go in. Secrets, generated data, and
machine-specific junk stay out.**

---

## Step 2 — Get the requirements.txt ready for hosting

Here's a wrinkle specific to this project. The core assistant has **zero** dependencies — it
runs on the Python standard library alone. So `requirements.txt` ships with everything
*commented out*. That's perfect for the CLI, but a host needs to know to install Streamlit, or
your web app won't start.

Before you deploy the app, open `requirements.txt` and make sure the hosting line is active.
At minimum a host needs:

```
streamlit>=1.30
```

Add these only if you want the extra toggles to work on the host:

- `requests>=2.28` — for the **live weather** checkbox (Open-Meteo, keyless).
- `litellm>=1.40` and `python-dotenv>=1.0` — for the **real LLM** toggle. These are only useful
  on the host if you *also* add an API key in Secrets (next step). Without a key the toggle
  silently falls back to the offline model, which is fine — so you can skip these entirely and
  the app still works.

A minimal, safe hosting `requirements.txt` is just `streamlit` plus `requests`. That runs the
whole app on the offline brain with live weather, no key anywhere. Commit that and you're done.

---

## Step 3 — Make the local repo and commit

From inside `build_from_scratch/` (the folder with `pyproject.toml` and `tool_agent/` in it):

```powershell
git init
git add .
git commit -m "Initial commit: Function-Calling Assistant (agent loop + 4 tools)"
```

Then the single most important check in this whole guide:

```powershell
git status
```

You want `nothing to commit, working tree clean`. You must **not** see `.env` anywhere. Confirm
the secret and the generated DB really are excluded:

```powershell
git ls-files | Select-String "company.db|.env$"
```

That should print nothing (an `.env.example` line is fine and expected). If `.env` shows up as
tracked, you committed your secret — see troubleshooting at the bottom before you push.

---

## Step 4 — Make the empty repo on GitHub and push

### 4a. Create the empty repo

1. On github.com, signed in, click **+** (top-right) then **New repository**.
2. Name it `function-calling-assistant` (lowercase, hyphens, no spaces).
3. Add a one-line description: *"An assistant that decides which tool to call to answer you —
   the agent loop (reason → act → observe) built from scratch, offline-first."*
4. Leave it **Public**.
5. Do **not** tick "Add a README", ".gitignore", or "license" — you need the repo completely
   empty or your first push collides with the files GitHub adds.
6. Click **Create repository**.

### 4b. Connect and push

Copy the repo URL from that page, then, still inside `build_from_scratch/`:

```powershell
git branch -M main
git remote add origin https://github.com/YOURNAME/function-calling-assistant.git
git push -u origin main
```

The first push opens a browser sign-in to authenticate. Do it. If it asks for a *password*
typed into the terminal, that won't work — GitHub turned off password auth years ago. Use the
browser sign-in, or a Personal Access Token (troubleshooting below). Refresh the repo page;
your files are there.

---

## Step 5 — Deploy the Streamlit app to a live URL

Two free paths. Pick one — Streamlit Community Cloud is the simplest; Hugging Face Spaces is a
nice second listing on your profile. Both read straight from your GitHub repo.

Either way, the app defaults to the **offline fake model**, so it runs with **no key**. You only
add a key if you want the "Real LLM (LiteLLM)" toggle to actually work.

### Path 1 — Streamlit Community Cloud

1. Make sure `requirements.txt` has `streamlit` uncommented (Step 2) and pushed.
2. Go to https://share.streamlit.io and sign in with GitHub. Authorize it to see your repos.
3. Click **New app** → **Deploy a public app from GitHub**.
4. Fill in:
   - **Repository:** `YOURNAME/function-calling-assistant`
   - **Branch:** `main`
   - **Main file path:** `app.py`  *(it lives at the repo root — `build_from_scratch/` is the root)*
5. Click **Deploy**. First build takes a couple of minutes while it installs Streamlit.
6. When it's live you get a URL like `https://your-app.streamlit.app`. Share that.

**To enable the real-model toggle (optional):** in the app's dashboard, open **Settings →
Secrets** and paste, in TOML form:

```toml
GEMINI_API_KEY = "your-free-key-from-aistudio.google.com/apikey"
```

Streamlit exposes secrets as environment variables, which is exactly what `has_api_key()` in
`tool_agent/llm.py` looks for. You'll also need `litellm` and `python-dotenv` in
`requirements.txt` for the real path to import. Reboot the app after saving secrets.

### Path 2 — Hugging Face Spaces (Streamlit SDK)

1. Go to https://huggingface.co, make an account.
2. Click your avatar → **New Space**.
3. Name it `function-calling-assistant`, pick a license, and choose **Streamlit** as the SDK.
   Leave the hardware on the free CPU tier.
4. A Space *is* a Git repo. The simplest way to fill it: clone the Space locally and copy your
   `build_from_scratch/` contents in, or push your existing repo to the Space's remote. A Space
   expects `app.py` and `requirements.txt` at its root — which is exactly your layout.
5. Hugging Face builds and serves it automatically. You get a public `...hf.space` URL.

**To enable the real-model toggle on a Space:** open the Space's **Settings → Variables and
secrets**, add a secret `GEMINI_API_KEY`, and make sure `litellm` + `python-dotenv` are in
`requirements.txt`. Secrets on Spaces also arrive as environment variables, so `has_api_key()`
picks them up. Without one, the toggle falls back to the offline model — no error, it just works.

---

## Step 6 — Add CI so the tests run on every push

CI (Continuous Integration) proves your 24 tests pass on a clean machine, not just your laptop,
every time you push. GitHub shows a green checkmark when they do. It's free on public repos, and
here it's especially clean: **the core has zero runtime dependencies, so CI installs pytest and
nothing else — no key, no network.**

In this hosting folder there's a ready-to-use workflow at `github_actions/ci.yml`. A workflow
only runs if it lives at `.github/workflows/` inside the repo. Copy it there. From the repo root
(`build_from_scratch/`):

```powershell
mkdir .github\workflows
copy ..\hosting\github_actions\ci.yml .github\workflows\ci.yml
```

(Adjust the source path to wherever this `hosting/` folder sits relative to your repo — it lives
one level up from `build_from_scratch/`, hence the `..\`.)

Open `.github\workflows\ci.yml` and read the comments — it's annotated line by line. Then:

```powershell
git add .github\workflows\ci.yml
git commit -m "Add GitHub Actions CI to run the 24 tests on every push"
git push
```

Go to your repo's **Actions** tab to watch it run: checkout, install Python, install pytest, run
the suite. Green means all 24 passed on GitHub's machine. If it goes red, click the failed step
and read the log bottom-up — the real error is usually in the last few lines.

Once it's green, add the status badge to the top of your README: on the workflow's Actions page,
the `...` menu has **Create status badge**, which gives you a line of markdown to paste.

---

## Step 7 — Pin the repo on your profile

By default your GitHub profile lists repos in no particular order. Pinning puts the good ones up
top. Go to `github.com/YOURNAME`, find **Customize your pins**, tick
`function-calling-assistant`, and save. Now it's the first thing a recruiter sees.

---

## Troubleshooting

**The deployed app crashes with `ModuleNotFoundError: streamlit`.** The host didn't install
Streamlit because it's commented out in `requirements.txt`. Uncomment `streamlit>=1.30`, commit,
push — the host redeploys automatically.

**The app runs but the "Real LLM" toggle says no key found.** Expected until you add one. Put
`GEMINI_API_KEY` in the host's Secrets (TOML on Streamlit Cloud, secrets on Spaces) *and* make
sure `litellm` and `python-dotenv` are in `requirements.txt`. The offline model works regardless
— a missing key is never fatal here.

**`query_database` errors about a missing database on the host.** The app calls
`generate_data.main()` on startup to build `data/company.db` when it's absent (the DB is
git-ignored). If it can't, confirm `generate_data.py` and the `tool_agent/` package are both at
the repo root and were pushed.

**You committed `.env` by accident.** Treat the key as compromised — go to the provider (Google
AI Studio, etc.) and **revoke/rotate it**, because if you pushed, it's already public. Then:

```powershell
git rm --cached .env
git commit -m "Remove committed .env"
git push
```

Confirm `.env` is in `.gitignore`. `git rm --cached` only removes it going forward — the key
still sits in your Git history, which is exactly why rotating it is the real fix.

**`error: failed to push` / push rejected.** The remote has commits your local repo doesn't —
almost always because you let GitHub add a README or license. Pull and replay:

```powershell
git pull origin main --rebase
git push
```

Next time, create the repo completely empty.

**Authentication fails on push.** GitHub no longer accepts your account password in the terminal.
Easiest fix: install the GitHub CLI from https://cli.github.com, run `gh auth login`, and follow
the browser prompts. Or generate a Personal Access Token (Settings → Developer settings → Personal
access tokens → Tokens (classic), `repo` scope) and paste it as the *password* when Git prompts.

**`git: command not found` after installing.** You're in a terminal that opened before the
install. Close every PowerShell window and open a fresh one.
