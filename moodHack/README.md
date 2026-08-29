# moodHack

moodHack is a web app for understanding and managing your emotions. You pick a mood
(50+ to choose from), get evidence-based coping mechanisms and music suggestions, chat
with an AI wellness assistant, and browse a library of articles. The assistant is a real
agent: it can reason through a request, call tools, and search a knowledge base instead of
just giving a canned response.

- **Frontend**: vanilla HTML/CSS/JS single-page app (no build step)
- **Backend**: Django 5, SQLite, JSON API
- **AI**: DeepSeek (OpenAI-compatible API) with a ReAct agent loop + tool calls + RAG

---

## Prerequisites

- Python 3.10+
- `pip`

That's it — there is no npm/build step anymore. The frontend is served by Django.

---

## Setup

From the project root (`moodHack/` — the folder containing `manage.py`):

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create your environment file from the template
#    On Windows:
copy .env.example .env
#    On macOS/Linux:
cp .env.example .env

# 3. Run migrations
python manage.py migrate

# 4. Load the knowledge base (mood data + starter articles)
python manage.py load_seed_data

# 5. Start the server
python manage.py runserver
```

Open <http://127.0.0.1:8000/> in your browser.

---

## Getting the AI chatbot working

The chat tab needs a DeepSeek API key. The mood explorer and article library work without
a key; only the chat requires it.

### 1. Get a DeepSeek API key

1. Go to <https://platform.deepseek.com/> and create an account (or log in).
2. Open **API Keys** in the dashboard.
3. Create a new key and copy it.

### 2. Put the key in your `.env` file

Open `.env` and fill in:

```env
DEEPSEEK_API_KEY=sk-your-actual-key-here
DEEPSEEK_MODEL=deepseek-chat
```

- `DEEPSEEK_MODEL` controls which model the app calls. `deepseek-chat` points at the
  current DeepSeek chat model. If you have a specific model id you want (for example a
  V4 model id your account supports), put that exact id here instead.
- Leave `DEEPSEEK_BASE_URL` as the default (`https://api.deepseek.com`) unless you are
  using a proxy/gateway.

### 3. Restart the server and test

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>, go to the **AI Chat** tab, and send a message like:

> I'm feeling anxious, can you suggest some coping mechanisms and music?

The assistant should call its tools (`get_mood_coping`, `search_knowledge_base`, or
`suggest_articles`) and return a formatted answer. You'll see a "Tool activity" note above
the chat box when it uses a tool.

---

## Common issues

- **"DEEPSEEK_API_KEY is not set"** — the `.env` file is missing or the key line is blank.
  Make sure `.env` is in the same folder as `manage.py`.
- **The chat says something went wrong** — check the terminal running the server; it will
  print the underlying error (usually an invalid key or the model id isn't available on
  your account).
- **Mood/Articles work but chat doesn't** — expected: only the chat calls DeepSeek.
- **Port already in use** — run on another port: `python manage.py runserver 8001`.

---

## Tests

```bash
python manage.py test
```

Tests mock the LLM, so they run without a DeepSeek key.

---

## Quick reference

| Command | What it does |
| --- | --- |
| `python manage.py migrate` | Create/update the database schema |
| `python manage.py load_seed_data` | Load mood resources + starter articles (safe to re-run) |
| `python manage.py scrape_articles` | Pull article metadata from configured sources |
| `python manage.py runserver` | Start the dev server |
| `python manage.py test` | Run the test suite |
