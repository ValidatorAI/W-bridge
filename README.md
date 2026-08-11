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

Each processed webhook message is stored in `message_logs`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).