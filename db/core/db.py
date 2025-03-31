from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
# import settings

username = 'Admin'
password = 'Admin'
host = '127.0.0.1'
port = '5432'
database = 'Admin'
schema = "rea_bot"

async_engine = create_async_engine(
    url=f'postgresql+asyncpg://{username}:{password}@127.0.0.1:5432/{database}',
    echo=False,
).execution_options(schema_translate_map={None:schema})

async_session_factory = async_sessionmaker(async_engine)

if __name__ == "__main__":
    """
    Check DB connection
    """
    print("DB")

    connection_string = f'postgresql+psycopg2://{username}:{password}@127.0.0.1:5432/{database}'

    engine = create_engine(connection_string)

    with engine.connect() as connection:
        inspector = inspect(connection)

        schemas = inspector.get_schema_names()

        for schema in schemas:
            print(schema)