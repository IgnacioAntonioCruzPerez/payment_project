import asyncio
import aio_pika

async def wait_for_rabbitmq():
    for i in range(10): 
        try:
            connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
            await connection.close() 
            print("✅ RabbitMQ connected")
            return  
        except Exception as e:
            print(f"⏳ RabbitMQ not ready... retry {i} | {e}")
            await asyncio.sleep(3) 

    raise Exception("❌ RabbitMQ connection failed after 10 attempts") 

async def main():
    await wait_for_rabbitmq() 

    connection = await aio_pika.connect_robust("amqp://guest:guest@rabbitmq:5672/")
    channel = await connection.channel()

    queue = await channel.declare_queue("payments", durable=True)

    print("👂 Waiting for messages...")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                print(f"📩 Received payment event: {message.body}")

if __name__ == "__main__":
    asyncio.run(main())