import os

class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@db:5432/payments"
    )
    API_KEY: str = os.getenv("API_KEY", "test-api-key")
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    PAYMENTS_QUEUE: str = os.getenv("PAYMENTS_QUEUE", "payments.new")
    PAYMENTS_DLQ: str = os.getenv("PAYMENTS_DLQ", "payments.new.dlq")

settings = Settings()