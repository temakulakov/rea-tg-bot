import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import asyncio
from db.models import School, Product, Students
import logging

async def get_or_create_school(session: AsyncSession, school_name: str, cache: dict) -> int:
    """Создает или возвращает существующую школу"""
    if not school_name:
        return None
    
    school_name = str(school_name).strip()
    if not school_name:
        return None
    
    if school_name in cache:
        return cache[school_name]
    
    result = await session.execute(select(School).where(School.name == school_name))
    school = result.scalars().first()
    
    if not school:
        school = School(name=school_name)
        session.add(school)
        await session.flush()
    
    cache[school_name] = school.id_school
    return school.id_school

def parse_fio(fio: str) -> tuple:
    """Парсит ФИО на составляющие с обработкой пустых значений"""
    if pd.isna(fio):
        return None, None, None
        
    parts = str(fio).strip().split()
    return (
        parts[0] if len(parts) > 0 else None,
        parts[1] if len(parts) > 1 else None,
        ' '.join(parts[2:]) if len(parts) > 2 else None
    )

async def process_data(async_session_factory):
    """Основная функция обработки данных"""
    df = pd.read_excel("file.xlsx", header=1, names=[
        "Секция", "Название проекта", "Школа_лидера", "Класс",
        "Формат выступления", "Дата_время", "Слот", "Лидер проекта",
        "Школа_уч1", "Участник 1", "Школа_уч2", "Участник 2", "Аудитория"
    ])

    #TODO: check
    
    async with async_session_factory() as session:
        school_cache = {}
        product_cache = {}

        # Первый проход: создание школ и продуктов
        for idx, row in df.iterrows():
            try:
                # Получаем общую школу для всех участников
                school_name = row['Школа_лидера']
                school_id = await get_or_create_school(session, school_name, school_cache)

                # Создаем продукт
                product = Product(
                    section=row['Секция'],
                    product_name=row['Название проекта'],
                    date_time=pd.to_datetime(row['Дата_время']) if pd.notna(row['Дата_время']) else None,
                    id_school=school_id,
                    location=row['Аудитория']
                )
                session.add(product)
                await session.flush()
                product_cache[row['Название проекта']] = product.id_product

            except Exception as e:
                logging.error(f"Ошибка в строке {idx}: {str(e)}")
                await session.rollback()

        # Второй проход: создание участников
        for idx, row in df.iterrows():
            try:
                product_id = product_cache.get(row['Название проекта'])
                if not product_id:
                    continue

                # Используем школу лидера для всех участников
                school_id = await get_or_create_school(
                    session, 
                    row['Школа_лидера'],
                    school_cache
                )

                # Обрабатываем всех участников
                for role in ['Лидер проекта', 'Участник 1', 'Участник 2']:
                    fio = row[role]
                    if pd.isna(fio):
                        continue

                    surname, name, father_name = parse_fio(fio)
                    
                    student = Students(
                        surname=surname,
                        name=name,
                        father_name=father_name,
                        grade=int(row['Класс']) if pd.notna(row['Класс']) else None,
                        id_school=school_id,
                        id_product=product_id
                    )
                    session.add(student)

                await session.flush()
                
            except Exception as e:
                logging.error(f"Ошибка в строке {idx}: {str(e)}")
                await session.rollback()

        await session.commit()

if __name__ == "__main__":
    # Настройка подключения (замените параметры на свои)
    async_engine = create_async_engine(
        "postgresql+asyncpg://user:password@localhost/dbname",
        echo=True  # Включить для отладки SQL-запросов
    )
    async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Запуск обработки
    asyncio.run(process_data(async_session_factory))