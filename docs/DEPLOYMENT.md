# Deployment

## Recommended free full-stack demo: Hugging Face Spaces

BanglaRAG includes a `Dockerfile` for a Hugging Face Docker Space. This is the best
free fit for the full app because the project uses `sentence-transformers`, which
needs more memory than many small free web-service tiers provide.

1. Create a new Hugging Face Space.
2. Select `Docker` as the SDK.
3. Push this repository to the Space repo, or upload the repository files there.
4. Add secrets/variables in the Space settings if you want real LLM output:
   - `LLM_PROVIDER=openai`, `gemini`, or `groq`
   - the matching API key such as `OPENAI_API_KEY`
5. Keep the default demo values if you want it to run without paid keys:
   - `LLM_PROVIDER=mock`
   - `USE_RERANKER=false`

The container listens on port `7860`, which is the default Space app port.

## Free fallback: Render

This repo also includes `render.yaml` for Render Blueprints. It deploys the FastAPI
app as a free web service with the same no-key demo defaults.

Important Render free-tier caveats:

- The service sleeps after inactivity and can take about a minute to wake up.
- The filesystem is ephemeral, so SQLite and Chroma data are not durable across
  restarts/redeploys.
- Free Postgres can persist relational data, but it expires after 30 days.

For a durable production deployment, use a paid service with persistent storage or
move the database/vector store to managed services.
