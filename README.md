# W-bridge

FastAPI bridge service for webhook forwarding.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

## Database

This project now uses:

- SQLite for persistence (`w_bridge.db` by default)
- SQLAlchemy as ORM
- Alembic for schema migrations

Default SQLite path behavior:

- Local run: `./w_bridge.db`
- Docker run: `/data/w-bridge/w_bridge.db`

You can override DB location with either `DATABASE_URL` (highest priority) or `SQLITE_DB_PATH`.

Example:

```bash
export DATABASE_URL="sqlite:///./w_bridge.db"
```

## Docker Persistent Volume

Mount a host directory or named volume to `/data/w-bridge` so data survives container recreation.

Example with a host folder:

```bash
docker run -d \
	-p 80:80 \
	-v $(pwd)/data:/data/w-bridge \
	--name w-bridge \
	your-image-name
```

Example with a named volume:

```bash
docker volume create wbridge_data
docker run -d \
	-v wbridge_data:/data/w-bridge \
	--name bridge_app \
	--network w_bridge \
	bridge
```

## Run Migrations

Apply the latest migrations:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

## API

Webhook endpoint:

```text
POST /webhook
```

### Webhook Authentication

The webhook requires a `token` query parameter.

Required environment variable:

- `MASTER_KEY_TOKEN` (must be set in `.env`)

Behavior:

- If `token` equals `MASTER_KEY_TOKEN`, the request is accepted and processed without bot lookup.
- Otherwise, `token` must match an active bot token from the `bots` table.

Example `.env` entry:

```dotenv
MASTER_KEY_TOKEN=some-master-key-token
```

Each processed webhook message is stored in `message_logs`.

## Hermes Multi-Profile Routing Requirements

If you enable multiplexing with:

```bash
echo "GATEWAY_MULTIPLEX_PROFILES=true" >> ~/.hermes/.env
```

make sure all of the following are in place.

- Set the flag on the default profile only (the default gateway becomes the multiplexer).
- Restart the default gateway after changing config:

```bash
hermes gateway restart
```

- For every named profile, set a distinct `API_SERVER_KEY` in `~/.hermes/profiles/<profile>/.env`.
- Keep port-binding HTTP platforms on the default profile only while multiplexing is enabled (for example `api_server`, `webhook`, `msgraph_webhook`, `feishu`, `wecom_callback`, `bluebubbles`, `sms`, `whatsapp_cloud`, `line`).
- Use profile-prefixed routes for named profiles: `/p/<profile>/...`.
- Use profile-matching auth keys:
	- `/v1/...` and `/p/default/...` use the default profile key.
	- `/p/<named-profile>/...` must use that named profile's key.

Verification examples:

```bash
# default profile
curl -H "Authorization: Bearer DEFAULT_KEY" http://127.0.0.1:8642/v1/health

# named profile
curl -H "Authorization: Bearer CODER_KEY" http://127.0.0.1:8642/p/coder/v1/health
```

Expected behavior:

- Default key on a named profile prefix returns `401`.
- Unknown/unconfigured profile prefix returns `404`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).