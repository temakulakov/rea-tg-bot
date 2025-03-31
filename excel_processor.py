import pandas as pd
from sqlalchemy import select,insert
from sqlalchemy.orm import query
import sqlalchemy as sql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import asyncio
from db.models import School, Product, Students, Base, Conference, Teacher, MasterClass
from db.core.db import async_session_factory,async_engine
import logging
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple

def parse_date_range(date_str: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Парсит строку с диапазоном дат и возвращает два объекта Timestamp (начало и конец).
    
    Пример входных данных: "22.04.2024 15:30-17:00"
    """
    if pd.isna(date_str):
        return None, None

    try:
        # Разделяем на начальную и конечную части
        start_str, end_str = date_str.split('-', 1)
        # print(start_str,"\n", end_str)
        # Парсим начальную дату-время
        start = pd.to_datetime(
            start_str.strip(), 
            format='%d.%m.%Y %H:%M', 
            dayfirst=True,
            utc=False
        )
        # print(start,"\n----",date_str.split('-', 1)[0].split(' ',1)[0]+f" {end_str}")
        
        # Извлекаем дату из начала и комбинируем с конечным временем
        end_time = pd.to_datetime(
            end_str.strip(), 
            format='%H:%M', 
        ).time()

        end = pd.to_datetime(
            start.strftime('%d.%m.%Y') + ' ' + end_time.strftime('%H:%M'),
            format='%d.%m.%Y %H:%M',
            dayfirst=True,
            utc=False
        )
        
        return start, end
    
    except Exception as e:
        print(f"Ошибка парсинга '{date_str}': {str(e)}")
        return None, None
    
async def clear_database(engine: AsyncSession, Base):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        #TODO: сделать сброс айдишек для автоинкремента
    
async def get_or_create_school(session: AsyncSession, school_name: str, cache: dict) -> int:
    """Создает или возвращает существующую школу"""
    if not school_name:
        return None
    
    school_name = str(school_name).strip()
    if not school_name:
        return None
    # print(f"PRIONTIRNT: {school_name}\n\n --- {cache}")
    if school_name in cache:
        return cache[school_name]
    
    result = await session.execute(select(School).where(School.school_name == school_name))
    school = result.scalars().first()
    if not school:
        school = School(school_name=school_name)
        session.add(school)
        await session.flush()
        # await session.commit()
        
    
    cache[school_name] = school.id
    return school.id

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

async def process_data(session: AsyncSession,filename: str = "file.xlsx"):
    """Основная функция обработки данных (все этапы)"""
    try:
        # Загрузка всех листов Excel
        df_projects = pd.read_excel(
            filename,
            sheet_name="Проекты",  # Предполагаемое имя листа
            header=0,
            names=[
                "Секция", "Название проекта", "Школа", "Класс", "Формат выступления",
                "Дата_время", "Слот", "Лидер проекта", "Школа_лидера", 
                "Участник 1", "Школа_уч1", "Участник 2", "Школа_уч2", "Аудитория"
            ]
        )

        df_conferences = pd.read_excel(
            "file.xlsx",
            sheet_name="Конференции",
            header=0,
            names=["Название", "Дата"]
        )
        
        df_masterclass = pd.read_excel(
            "file.xlsx",
            sheet_name="МК",
            header=0,
            names=["Название мастер-класса", "Дата_время", "Ссылка", "Локация", "Конференция"]
        )

        df_teachers = pd.read_excel(
            "file.xlsx",
            sheet_name="Учителя",
            header=0,
            names=["ФИО", "Школа", "login", "password"]
        )
        
        df_admin = pd.read_excel(
            "file.xlsx",
            sheet_name="admin",
            header=0,
            names=["login", "password"]
        )

        async with session.begin():
            # 1. Обработка конференций
            conference_cache = {}
            for idx, row in df_conferences.iterrows():
                conference = Conference(
                    name=row['Название'],
                    date=pd.to_datetime(row['Дата'])
                )
                session.add(conference)
                # print(conference.id,"\n================================================================")
                await session.flush()
                # print(conference.id,"\n================================================================")
                conference_cache[row['Название']] = conference.id

            # 2. Обработка мастер-классов
            masterclass_cache = {}
            for idx, row in df_masterclass.iterrows():
                conference_id = conference_cache.get(row['Конференция'])
                if not conference_id:
                    raise ValueError(f"Конференция {row['Конференция']} не найдена")
                
                start_time, end_time = parse_date_range(row['Дата_время'])
                masterclass = MasterClass(
                    name=row['Название мастер-класса'],
                    date_time_start=start_time,
                    date_time_end=end_time,
                    url_link=row['Ссылка'],
                    location=str(row['Локация']),
                    id_conference=conference_id
                )
                session.add(masterclass)
                await session.flush()
                masterclass_cache[row['Название мастер-класса']] = masterclass.id
            for idx, row in df_admin.iterrows():
                teacher = Teacher(
                    login=str(row['login']),
                    admin=True,
                )
                teacher.set_password(row['password'])
                session.add(teacher)
            # 3. Обработка учителей (оригинальный кэш школ)
            school_cache = {}
            for idx, row in df_teachers.iterrows():
                school_id = await get_or_create_school(
                    session,
                    row['Школа'],
                    school_cache
                )
                
                surname, name, father_name = parse_fio(row['ФИО'])
                
                teacher = Teacher(
                surname=surname,
                name=name,
                father_name=father_name,
                id_school=school_id,
                login=str(row['login']),  # Берем логин из столбца "login"
                )
                teacher.set_password(row['password'])  # Устанавливаем пароль из столбца "password"

                session.add(teacher)
                # print(teacher.password)
                # print("\n")
            # 4. Оригинальная обработка проектов и студентов 
            school_cache_projects = {}
            product_cache = {}
            
            # Первый проход: проекты
            for idx, row in df_projects.iterrows():
                school_id = await get_or_create_school(
                    session,
                    row['Школа_лидера'],
                    school_cache_projects
                )
                start_time, end_time = parse_date_range(row['Дата_время'])
                product = Product(
                    section=str(row['Секция']),
                    product_name=str(row['Название проекта']),
                    date_time_start=start_time,
                    date_time_end=end_time,
                    id_school=school_id,
                    location=str(row['Аудитория']),
                    project_format=str(row['Формат выступления']),
                )
                session.add(product)
                await session.flush()
                product_cache[row['Название проекта']] = product.id
            
            # Второй проход: студенты
            for idx, row in df_projects.iterrows():
                product_id = product_cache.get(row['Название проекта'])
                if not product_id:
                    continue

                school_id = school_cache_projects.get(row['Школа_лидера'])
                if not school_id:
                    continue

                students_data = []
                for role in ['Лидер проекта', 'Участник 1', 'Участник 2']:
                    fio = row[role]
                    if pd.isna(fio):
                        continue

                    surname, name, father_name = parse_fio(fio)
                    students_data.append({
                        "surname": surname,
                        "name": name,
                        "father_name": father_name,
                        "grade": row['Класс'],
                        "id_school": school_id,
                        "id_product": product_id
                    })

                if students_data:
                    await session.execute(insert(Students), students_data)

    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        await session.rollback()
        raise  
    
    except SQLAlchemyError as e:
        logging.error(f"Ошибка базы данных: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Общая ошибка: {str(e)}")
        raise

async def start_parse_excel():
    filename = "file.xlsx"
    try:
        # Очистка и инициализация БД
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Основной процесс
        async with async_session_factory() as session:
            await process_data(session,filename)
        logging.info("Файл загружен")
        print(f"\nФайл загружен - {filename}\n")
    except Exception as e:
        logging.critical(f"Критическая ошибка: {str(e)}")
    finally:
        await async_engine.dispose()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    asyncio.run(start_parse_excel())
    # Настройка подключения (замените параметры на свои)
    # async_engine = create_async_engine(
    #     "postgresql+asyncpg://user:password@localhost/dbname",
    #     echo=True  # Включить для отладки SQL-запросов
    # )
    # async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)

   
    