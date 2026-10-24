import asyncio

from sqlalchemy import text

from app.core.db import engine


async def main() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        print(result.scalar_one())
    await engine.dispose()


asyncio.run(main())
