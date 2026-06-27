# CV AI: Conversational

🚀 **Live Demo:** [https://cv-ai-conversational.onrender.com/](https://cv-ai-conversational.onrender.com/)

Production-grade Voice AI Assistant inspired by **ChatGPT Voice Mode**, featuring real-time speech recognition, LLM reasoning with tool calling, streaming TTS, and a photorealistic HeyGen streaming avatar.

## Features

- **Voice-first interface** — microphone input with live waveform visualization
- **Speech-to-Text** — OpenAI Whisper (Large-v3 via API)
- **LLM reasoning** — GPT-4.1 / GPT-5 with OpenAI Function Calling
- **Tool calling** — weather, news, stocks, Wikipedia, web search, current time
- **Content moderation** — OpenAI Moderation API guardrails
- **Text-to-Speech** — ElevenLabs streaming TTS
- **Photorealistic avatar** — HeyGen Streaming Avatar with lip sync
- **Low latency** — WebSockets, streaming LLM/TTS, Redis caching, parallel API calls
- **Beautiful UI** — glassmorphism, dark/light mode, Framer Motion animations
- **Production ready** — Docker, Vercel + Railway deployment, tests, structured logging

## Architecture

```
Microphone → STT (Whisper) → Moderation → LLM + Tools → TTS (ElevenLabs) → Avatar (HeyGen) → Playback
                                    ↕
                              WebSocket (streaming)
                                    ↕
                              Redis Cache + SQLite
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15+, React, TypeScript, Tailwind CSS, Framer Motion, shadcn/ui |
| Backend | FastAPI, Python 3.12, AsyncIO |
| AI | OpenAI Whisper, GPT-4.1, Function Calling, Moderation |
| Speech | ElevenLabs TTS |
| Avatar | HeyGen Streaming Avatar API |
| Search | Tavily Search API |
| Weather | OpenWeather API |
| Stocks | Finnhub API |
| Database | SQLite (aiosqlite) |
| Cache | Redis |
| Deploy | Vercel (frontend) + Railway (backend) |


## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- Redis (or Docker)
- API keys: OpenAI, ElevenLabs, Tavily (optional: HeyGen, OpenWeather, Finnhub)

### 1. Clone & configure

```bash
git clone <repo-url>
cd ABC

# Backend env
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Frontend env
cp frontend/.env.local.example frontend/.env.local
```

### 2. Run with Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/docs

### 3. Run locally (development)

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
mkdir -p data
uvicorn app.main:app --reload --port 8000
```

**Redis:**

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key (Whisper, GPT, Moderation) |
| `OPENAI_MODEL` | No | Default: `gpt-4.1` |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs TTS |
| `ELEVENLABS_VOICE_ID` | No | Default voice ID |
| `HEYGEN_API_KEY` | No | HeyGen avatar (fallback UI if missing) |
| `HEYGEN_AVATAR_ID` | No | HeyGen avatar ID |
| `TAVILY_API_KEY` | No | Web search |
| `OPENWEATHER_API_KEY` | No | Weather tool |
| `FINNHUB_API_KEY` | No | Stock prices |
| `REDIS_URL` | No | Default: `redis://localhost:6379/0` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend URL (default: `http://localhost:8000`) |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL (default: `ws://localhost:8000`) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/chat/voice` | Voice input (multipart audio) |
| POST | `/api/v1/chat/text` | Text chat |
| GET | `/api/v1/chat/conversations` | List conversations |
| WS | `/ws/voice` | Streaming voice/text pipeline |
| POST | `/api/v1/avatar/session` | Create HeyGen session |
| GET/PATCH | `/api/v1/settings` | User settings |

## Voice Pipeline

1. **Microphone** — browser MediaRecorder captures audio
2. **STT** — Whisper transcribes speech (<500ms target)
3. **Moderation** — content safety check
4. **LLM** — GPT processes intent, calls tools in parallel
5. **TTS** — ElevenLabs streams audio (<700ms target)
6. **Avatar** — HeyGen lip-syncs response
7. **Playback** — audio + video rendered in browser

**Target total latency: <2 seconds**

## Tools (Function Calling)

The LLM automatically selects tools based on user intent:

| Tool | Trigger Examples |
|------|-----------------|
| `get_weather` | "What's the weather in Tokyo?" |
| `web_search` | "Latest AI news today" |
| `get_news` | "News about Tesla" |
| `wikipedia_search` | "Tell me about quantum computing" |
| `get_current_time` | "What time is it in New York?" |
| `get_stock_price` | "Apple stock price" |

## Guardrails

Requests are screened via OpenAI Moderation API. Blocked categories:

- Hate speech & harassment
- Violence & self-harm
- Illegal activities
- Adult content

Blocked requests receive a polite refusal, spoken via TTS.

## Testing

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pytest -v

# Frontend lint
cd frontend
npm run lint
npm run build
```




## License

MIT
