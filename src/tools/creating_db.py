import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import Config

# Не удалять. Используется для подгрузки всех моделей БД
from src.modules.db_models import *
from src.core.database.database import Base

async def create_database():
    """Создает базу данных и все таблицы в ней (если существует, то ничего не произойдёт) """
    # Сначала подключаемся к серверу PostgreSQL без указания конкретной базы
    conf = Config()

    engine = create_async_engine(conf.db_connection.postgres_server_url, isolation_level="AUTOCOMMIT")

    try:
        # Проверяем существование базы данных и создаем если ее нет
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{conf.env.db_name}'")
            )
            database_exists = result.scalar() == 1

            if not database_exists: # если БД нет
                logging.info(f"Creating database {conf.env.db_name}...")
                await conn.execute(text(f"CREATE DATABASE {conf.env.db_name}"))
                logging.info(f"Database {conf.env.db_name} created successfully")
            else:
                logging.info(f"Database {conf.env.db_name} already exists")
    except Exception as e:
        logging.error(f"Error checking/creating database: {e}")
        raise
    finally:
        await engine.dispose()

    # создаем таблицы в целевой базе данных
    engine = create_async_engine(conf.db_connection.sql_db_url)
    try:
        async with engine.begin() as conn:
            logging.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            # Применяем миграции для добавленных колонок к существующим таблицам
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT;")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS slug VARCHAR(150) UNIQUE;")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS product_type VARCHAR(50) DEFAULT 'rope';")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS index INTEGER DEFAULT 0;")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
            )
            await conn.execute(
                text("ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;")
            )
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()



if __name__ == "__main__":
    asyncio.run(create_database())
