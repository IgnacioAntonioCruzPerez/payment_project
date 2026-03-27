import aio_pika
import json
from app.core.config import settings


async def publish_message(message: dict):
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(settings.PAYMENTS_QUEUE, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key=queue.name,
        )
