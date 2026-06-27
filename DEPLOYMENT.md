# Production Deployment Guide

This guide covers deploying the Voice AI Assistant to **Vercel** (frontend) and **Railway** (backend + Redis).

## Prerequisites

- GitHub repository with the project
- Accounts on [Vercel](https://vercel.com), [Railway](https://railway.app)
- API keys for all services (see `backend/.env.example`)

## Step 1: Deploy Backend to Railway

### Create Project

1. Log in to Railway and click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose your repository

### Configure Service

1. Set **Root Directory** to `backend` (or use `railway.toml` at repo root)
2. Railway auto-detects the Dockerfile

### Add Redis

1. In your Railway project, click **+ New**
2. Select **Database → Redis**
3. Copy the `REDIS_URL` from Redis service variables

### Environment Variables

Add these in Railway → Service → Variables:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
HEYGEN_API_KEY=...
HEYGEN_AVATAR_ID=...
TAVILY_API_KEY=...
OPENWEATHER_API_KEY=...
FINNHUB_API_KEY=...
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=https://your-app.vercel.app
DEBUG=false
```

### Deploy

Railway deploys automatically on push. Note your public URL:
`https://your-backend.up.railway.app`

Verify: `GET https://your-backend.up.railway.app/api/v1/health`

## Step 2: Deploy Frontend to Vercel

### Import Project

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New → Project**
3. Import your GitHub repo
4. Set **Root Directory** to `frontend`

### Environment Variables

```
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.up.railway.app
```

> Use `wss://` (not `ws://`) for secure WebSocket in production.

### Deploy

Click **Deploy**. Vercel builds and hosts at `https://your-app.vercel.app`.

## Step 3: Post-Deployment Checklist

- [ ] Health endpoint returns `"status": "healthy"`
- [ ] CORS allows your Vercel domain
- [ ] Microphone permission works (HTTPS required)
- [ ] Voice recording → transcription → response works
- [ ] WebSocket streaming works (text input)
- [ ] HeyGen avatar connects (if API key configured)
- [ ] Tools work (try "What's the weather in London?")

## Docker Self-Hosted

For VPS or local production:

```bash
# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env

# Start all services
docker compose up -d --build

# View logs
docker compose logs -f backend
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Redis: localhost:6379

## Monitoring

### Backend Logs

Railway provides built-in log streaming. Locally:

```bash
docker compose logs -f backend
```

Structured logs use `structlog` with JSON-friendly output.

### Health Monitoring

Set up uptime monitoring on:
```
GET /api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "Voice AI Assistant",
  "services": {
    "openai": true,
    "elevenlabs": true,
    "heygen": true,
    "tavily": true,
    "openweather": true
  }
}
```

## Scaling

### Railway

- Increase replicas in Railway service settings
- Redis handles shared caching across instances
- SQLite is file-based — for multi-instance, migrate to PostgreSQL

### Latency Optimization

1. Use `eleven_turbo_v2_5` model (already configured)
2. Enable Redis caching (weather, search, stocks)
3. Use WebSocket path for text (streaming)
4. Deploy backend close to users (Railway regions)
5. Set `OPENAI_MODEL=gpt-4.1` for speed vs quality balance

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS errors | Add Vercel URL to `CORS_ORIGINS` |
| WebSocket fails | Use `wss://` and ensure Railway supports WS |
| No audio playback | Check ElevenLabs API key and voice ID |
| Avatar not loading | Verify HeyGen API key; fallback UI still works |
| Slow responses | Check Redis connection; verify API key quotas |
| Moderation blocks valid input | Review OpenAI moderation settings |

## Security Notes

- Never commit `.env` files
- Use Railway/Vercel secret management
- All API keys are server-side only (except public URLs)
- Moderation runs on every user input
- HTTPS enforced in production (Vercel + Railway)
