# W-bridge

FastAPI bridge service that mirrors the webhook behavior from `app.js`.

## Run

Install dependencies:

```bash
pip install -r requirement.txt
```

Start server on port 4141:

```bash
uvicorn main:app --host 0.0.0.0 --port 4141
```

Webhook endpoint:

```text
POST /webhook
```