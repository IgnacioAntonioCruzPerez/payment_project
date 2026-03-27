import aio_pika
import json

RABBIT_URL = "amqp://guest:guest@rabbitmq/"


async def publish_message(message: dict):
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    queue = await channel.declare_queue("payments", durable=True)

    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(message).encode()
        ),
        routing_key=queue.name,
    )

    await connection.close()