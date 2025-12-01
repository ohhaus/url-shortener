import asyncio

from src.cache.redis import redis_manager


async def check_redis():
    await redis_manager.init()

    try:
        # Получить все ключи
        keys = await redis_manager.get_client().keys('*')
        print('Все ключи в Redis:', keys)

        # Проверить конкретные ключи
        for key in keys:
            value = await redis_manager.get_client().get(key)
            ttl = await redis_manager.get_client().ttl(key)
            print(f'Ключ: {key}, Значение: {value}, TTL: {ttl}')

    finally:
        await redis_manager.close()


if __name__ == '__main__':
    asyncio.run(check_redis())
