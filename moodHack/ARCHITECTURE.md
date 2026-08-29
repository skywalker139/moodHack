# moodHack — Architecture & Complete Flow

This document assumes you know how web apps work (HTTP, databases, APIs, a bit of Python
and JavaScript) but have never seen this project before. It explains what the app does,
what it's built from, and exactly how a request flows through it.

---

## 1. What this project is

moodHack is a Django web application for emotional wellness. A user can:

1. **Explore moods** — pick from a taxonomy of 50+ emotions and get coping mechanisms,
   music suggestions, and resource links.
2. **Chat with an AI assistant** — a DeepSeek-backed agent that can reason, call tools,
   and retrieve from a knowledge base (RAG).
3. **Browse articles** — a searchable library of curated mental-wellness reads.

The original project made a single hardcoded call to Google Gemini ("I am feeling X,
suggest coping mechanisms") and discarded the response. This version replaces that with a
proper agentic backend and a real three-tab UI.

---

## 2. Tech stack

| Layer | Technology | Why |
| --- | --- | --- |
| Backend framework | Django 5.0 | Routing, ORM, admin, migrations |
| Database | SQLite | Zero-config local store |
| AI provider | DeepSeek (OpenAI-compatible API) | Cheap, capable, supports function calling |
| AI SDK | `openai` Python SDK | Points at DeepSeek's OpenAI-compatible endpoint |
| Agent pattern | ReAct loop | Model reasons → calls tools → observes → repeats |
| Retrieval | Lexical (term-frequency) RAG | No vector store needed for the seed corpus |
| Frontend | Vanilla HTML/CSS/JS SPA | No build toolchain |
| Config/secrets | `python-dotenv` + `.env` | Keys out of source control |

Key dependencies (see `requirements.txt`):

```
django, django-cors-headers, openai, python-dotenv, requests, beautifulsoup4
```

---

## 3. Repository layout

```
moodHack/
├── manage.py                  # Django entrypoint
├── requirements.txt           # Python dependencies (pinned)
├── .env.example               # Template for secrets/config
├── moodHack/                  # Django project config
│   ├── settings.py            # Installed apps, DB, static, CORS
│   ├── urls.py                # Top-level routes
│   ├── wsgi.py / asgi.py      # Server entrypoints
├── api/                       # The Django app
│   ├── models.py              # ORM models
│   ├── views.py               # HTTP request handlers (JSON API + SPA)
│   ├── urls.py                # App routes
│   ├── admin.py               # Django admin registrations
│   ├── tests.py               # Unit/integration tests
│   ├── seed_data.py           # Single source of truth for moods + articles
│   ├── migrations/            # Schema history
│   ├── services/              # The AI/agent layer (no HTTP here)
│   │   ├── llm.py             # DeepSeek client
│   │   ├── agent.py           # ReAct loop
│   │   ├── tools.py           # Tool schemas + implementations
│   │   └── rag.py             # Retrieval over the knowledge base
│   └── management/commands/   # Custom CLI commands
│       ├── load_seed_data.py
│       └── scrape_articles.py
└── frontend/                  # The SPA (served by Django)
    ├── index.html             # SPA shell (3 tabs)
    ├── style.css              # Design system
    └── app.js                 # All client-side logic
```

---

## 4. Data model

- **`ChatSession`** — one conversation. Has a UUID `session_id` and a `created_at`.
- **`ChatMessage`** — a single message in a session. Fields:
  - `session` (FK → `ChatSession`)
  - `role` (`user` / `assistant` / `system` / `tool`)
  - `content` (the text)
  - `tool_calls` (JSON — a record of tool activity for this assistant turn)
  - `articles` (JSON — articles the assistant cited)
- **`MoodResource`** — one mood's data: name, primary emotion, description,
  coping mechanisms, music suggestions, resource links, keywords.
- **`Article`** — a title, URL, description, topics, and source.
- **`MoodJournal`** — a saved mood reflection (`mood` + `note`).

Relationships: a `ChatSession` has many `ChatMessage`s. `MoodResource`, `Article`, and
`MoodJournal` are independent lookup/append tables.

---

## 5. The agent layer (the interesting part)

The backend is split so that HTTP handling and AI logic are decoupled:

### `services/llm.py`

`LLMClient` wraps the DeepSeek API. Its one important method:

```python
chat(messages, tools=None, json_mode=False) -> {
    "text": str,
    "tool_calls": [...],
    "usage": {...},
    "finish_reason": str,
}
```

It reads `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, and `DEEPSEEK_BASE_URL` from the
environment, points the OpenAI SDK at DeepSeek's base URL, adds retries + timeouts, and
normalizes the response so the rest of the app doesn't care which provider is behind it.

### `services/tools.py`

Defines the four tools the model can call. Each has a JSON Schema (so the model knows the
exact arguments) and a Python callable:

| Tool | Purpose |
| --- | --- |
| `search_knowledge_base(query)` | RAG search over moods + articles |
| `get_mood_coping(mood)` | Structured coping + music for a specific mood |
| `suggest_articles(topic)` | Find articles on a topic |
| `save_mood_journal(mood, note)` | Persist a mood journal entry |

### `services/rag.py`

Retrieval without a vector database. It tokenizes text, drops stopwords, and scores
documents by term-frequency overlap. The seed corpus is small enough that this works
well; a future upgrade would swap in embeddings + a vector store behind the same
`search_knowledge_base` interface.

### `services/agent.py`

The ReAct loop. Given a user message and optional history:

1. Send `[system, ...history, user]` to the LLM with the tool definitions.
2. If the model returns `tool_calls`:
   - Record the assistant's tool-call message.
   - Execute each tool server-side.
   - Append each result as a `tool` message.
   - Go back to step 1.
3. If the model returns plain text (no tool calls), that's the final answer.
4. Safety valve: stop after `MAX_ITERATIONS` (6) and force a final answer.

The system prompt gives the model its persona and rules (empathetic, cite article URLs,
encourage professional help in a crisis, respond in markdown).

---

## 6. HTTP API

All JSON endpoints are under `/api/`. The root `/` serves the SPA.

| Method | Path | Body / query | What it does |
| --- | --- | --- | --- |
| GET | `/` | — | Serve the SPA (`index.html`) |
| POST | `/api/chat/` | `{message, session_id?}` | Run the agent, persist the exchange, return `{reply, tool_calls, articles, session_id}` |
| POST | `/api/mood/` | `{mood}` | Return structured coping/music/links for a mood |
| GET | `/api/moods/` | — | Return the full mood taxonomy (primary → secondary → tertiary) |
| GET | `/api/articles/` | — | List the article library |
| POST | `/api/articles/refresh/` | — | Run the scraper to pull new articles |
| POST | `/api/journal/` | `{mood, note?}` | Save a mood journal entry |
| GET | `/api/history/` | `?session_id=` | Return a session's messages |

Notes:

- `session_id` is a UUID. If you don't send one, the server creates a new session and
  returns its id — send that id back on subsequent messages to keep the conversation.
- The JSON API is CSRF-exempt because the SPA is served without a session cookie. This is
  a dev posture; a production deployment should serve the SPA through Django templates and
  re-enable CSRF.

---

## 7. End-to-end flow: mood explorer

1. User opens `/`, which renders `frontend/index.html` (the SPA shell).
2. `app.js` loads and calls `GET /api/moods/`.
3. `views.moods()` reads the taxonomy from `seed_data.py` and returns it as JSON.
4. The client renders primary-emotion chips; clicking one fetches its secondary moods,
   then its tertiary moods.
5. Clicking a specific mood calls `POST /api/mood/` with `{mood: "ANXIOUS"}`.
6. `views.mood()` calls `rag.get_mood_resource()`, which reads `MoodResource` from SQLite.
7. The view returns structured coping mechanisms, music, and resource links; the client
   renders them as formatted cards.

No LLM is involved in this flow — it's pure retrieval from the seeded database.

---

## 8. End-to-end flow: AI chat (with tool calls)

1. User types "I'm anxious, help me cope" in the AI Chat tab and submits.
2. `app.js` POSTs to `/api/chat/` with `{message, session_id}`.
3. `views.chat()`:
   - Looks up or creates the `ChatSession`.
   - Persists the user's `ChatMessage`.
   - Builds prior turn history from the DB.
   - Calls `Agent.run(message, history)`.
4. `Agent.run()` enters the ReAct loop (see §5). The model decides to call
   `get_mood_coping(mood="ANXIOUS")`.
5. The agent executes that tool, which returns the `MoodResource` data from SQLite.
6. The tool result is appended to the conversation; the model produces a final markdown
   answer citing coping mechanisms, music, and any relevant articles.
7. `views.chat()` persists the assistant's reply (with tool trace and cited articles) and
   returns the full result to the client.
8. `app.js` renders the assistant message as markdown and shows a "Tool activity" note.

---

## 9. End-to-end flow: articles

1. User opens the Articles tab; `app.js` calls `GET /api/articles/`.
2. `views.articles()` returns all `Article` rows.
3. The client renders a searchable card grid (client-side filtering).
4. Clicking "Refresh from web" POSTs to `/api/articles/refresh/`, which runs the
   `scrape_articles` management command to fetch metadata from a small allowlist of
   sources and upsert new `Article` rows.

---

## 10. Seeding & the scraper

- `seed_data.py` is the single source of truth for the mood taxonomy and the starter
  articles. `load_seed_data` upserts `MoodResource` and `Article` rows from it, so it's
  safe to re-run (idempotent).
- `scrape_articles` (optional) uses `requests` + `BeautifulSoup` to pull title/description
  metadata from a hardcoded allowlist of wellness pages and upsert them into `Article`.
  It's triggered manually or via `/api/articles/refresh/`.

---

## 11. Configuration

Everything is driven by `.env` (see `.env.example`):

```env
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DEEPSEEK_API_KEY=...
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`settings.py` reads these with safe defaults. `DEEPSEEK_MODEL` is the only knob you'll
usually touch — set it to whichever DeepSeek model id your account supports.

---

## 12. What's deliberately out of scope (for now)

- **Streaming responses** — the agent returns the full reply; no token streaming yet.
- **Vector/embedding search** — lexical retrieval is good enough for the seed corpus.
- **Real user authentication** — sessions are anonymous UUIDs; the schema is ready for a
  user FK later.
- **Deployment hardening** — `DEBUG`, CORS, and CSRF are configured for local dev.
