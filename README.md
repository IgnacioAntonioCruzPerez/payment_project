# Async Payment Processing Service

Microservice for asynchronous payment processing:

- API receives payment requests.
- Payment event is written to outbox in the same DB transaction.
- Outbox worker publishes events to RabbitMQ queue `payments.new`.
- Consumer processes payments asynchronously and sends webhook notifications.
- Failed processing after 3 attempts is moved to DLQ `payments.new.dlq`.

## Tech stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async)
- PostgreSQL
- RabbitMQ + FastStream
- Alembic (migrations)
- Docker + docker-compose

## Domain model

### Payment

- `id` (UUID)
- `amount` (decimal)
- `currency` (`RUB | USD | EUR`)
- `description` (string)
- `metadata` (json, optional)
- `status` (`pending | succeeded | failed`)
- `idempotency_key` (unique)
- `webhook_url`
- `created_at`, `processed_at`

### Outbox

- `id` (UUID)
- `event_type`
- `payload`
- `status`
- `attempts`
- `created_at`

## API

All endpoints require header:

- `X-API-Key: test-api-key` (or your configured `API_KEY`)

### Create payment

- `POST /api/v1/payments`
- Required header: `Idempotency-Key`
- Body:
  - `amount`
  - `currency` (`RUB | USD | EUR`)
  - `description`
  - `metadata` (optional object)
  - `webhook_url`
- Response: `202 Accepted`

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/payments" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -H "Idempotency-Key: idem-001" \
  -d '{
    "amount": 99.90,
    "currency": "USD",
    "description": "Order #123",
    "metadata": {"order_id": "123"},
    "webhook_url": "https://webhook.site/your-id"
  }'
```

### Get payment

- `GET /api/v1/payments/{payment_id}`

Example:

```bash
curl "http://localhost:8000/api/v1/payments/<payment_id>" \
  -H "X-API-Key: test-api-key"
```

## Processing flow

1. API creates `payments` row with status `pending`.
2. API creates `outbox` row (`event_type=payments.new`) in the same transaction.
3. Outbox worker publishes event to RabbitMQ queue `payments.new`.
4. Consumer receives event and:
   - emulates processing delay `2-5` seconds,
   - sets result status (`90% succeeded`, `10% failed`),
   - updates `processed_at`,
   - sends webhook with retry policy.
5. On processing failure:
   - retries up to `3` attempts (exponential delay in webhook sender),
   - sends message to `payments.new.dlq` after final failure.

## Run with Docker

```bash
docker compose up --build
```

This starts:

- `db` (PostgreSQL)
- `rabbitmq` (RabbitMQ + management UI)
- `api` (runs `alembic upgrade head` on startup, then FastAPI)
- `worker` (outbox publisher)
- `consumer` (payment processor)

Services:

- API: `http://localhost:8000`
- RabbitMQ UI: `http://localhost:15672` (login `guest` / `guest`)

## Environment variables

- `API_KEY` (default: `test-api-key`)
- `DATABASE_URL` (default in code: `postgresql+asyncpg://postgres:postgres@db:5432/payments`)
- `RABBITMQ_URL` (default: `amqp://guest:guest@rabbitmq:5672/`)
- `PAYMENTS_QUEUE` (default: `payments.new`)
- `PAYMENTS_DLQ` (default: `payments.new.dlq`)

## Migrations

Alembic is configured in `alembic.ini`.

Initial migration creates:

- `payments`
- `outbox`

Manual commands (optional):

```bash
alembic upgrade head
alembic downgrade -1
```

## Acceptance criteria checklist

- [x] Payments API: create/get
- [x] `Idempotency-Key` support
- [x] Outbox pattern (`payments` + `outbox` in one transaction)
- [x] Async worker publishes `payments.new`
- [x] One consumer handles processing + webhook
- [x] Retry behavior and DLQ after 3 failed attempts
- [x] Static API key auth via `X-API-Key`
- [x] Docker compose with `postgres`, `rabbitmq`, `api`, `worker`, `consumer`
- [x] README with run and examples
