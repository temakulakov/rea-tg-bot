from sqlalchemy import Integer, and_, func, insert, select, text, update
from sqlalchemy.orm import aliased

from db.core.db import async_engine,async_session_factory
from db.models import School,Product,Conference,MasterClass,Students,Teacher
from db.models import Base
from functools import wraps
from fastapi import Request,Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

# def auth_required(func):
#     @wraps(func)
#     async def wrapper(request: Request, *args, **kwargs):
#         # Получаем учителя из запроса
#         teacher = await get_current_teacher(request)
        
#         if not teacher:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="Требуется авторизация",
#             )
            
#         kwargs["teacher"] = teacher
#         return await func(*args, **kwargs)
        
#     return wrapper

class AsyncORM:
    @staticmethod
    async def create_tables():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def insert_students():
        async with async_session_factory() as session:
            worker_jack = Students(name="Jack")
            worker_michael = Students(name="Michael",surname="Xer",father_name="Yux")
            session.add_all([worker_jack, worker_michael])
            # flush взаимодействует с БД, поэтому пишем await
            await session.flush()
            await session.commit()

    @staticmethod
    async def select_students():
        async with async_session_factory() as session:
            query = select(Students)
            result = await session.execute(query)
            students = result.scalars().all()
            students_data = [student.to_dict() for student in students]
            print(f"{students_data=}")
            
            return students_data

    @staticmethod
    async def auth_student(first_name,second_name):
        async with async_session_factory() as session:
            clean_surname = second_name.strip().lower()
            clean_name = first_name.strip().lower()
            print(clean_name,clean_surname)
            query = select(
                Students,
                School.school_name,
                Product
            ).join(
                School, Students.id_school == School.id
            ).join(
                Product, Students.id_product == Product.id
            ).where(
                func.lower(Students.surname) == clean_surname,
                func.lower(Students.name) == clean_name
            )

            result = await session.execute(query)
            student_data = result.all()
            print(student_data)
            data: list[Students] = []
            for student in student_data:
                st = {
                    "id": student.Students.id,
                    "second_name": student.Students.surname,
                    "name": student.Students.name,
                    "father_name": student.Students.father_name,
                    "school_name": student.school_name,
                    "project_name": student.Product.product_name,
                    "school_class": student.Students.grade,
                    "project_slot": student.Product.location,
                    "project_format": student.Product.project_format,
                    "project_datetime_start": student.Product.date_time_start,
                    "project_datetime_end": student.Product.date_time_end,
                    "image_url": student.Product.url_scheme,
                    
                }
                data.append(st)
            import pprint
            pprint.pprint(data)
            if student_data:
                return {
                    "status": "success",
                    "data": data
                }
            return {"status": "not_found", "message": "Студент не найден"}


    @staticmethod
    async def auth_teacher(login, password):
        async with async_session_factory() as session:
            # Ищем учителя по логину
            # query = select(
            #     Teacher,
            #     School,
            #     Product,
            #     Students
            # ).where(
            #     Teacher.login == login
            # ).join(
            #     School, Teacher.id_school == School.id
            # ).join(
            #     Students, Teacher.id_school == Students.id_school
            # ).join(
            #     Product, Students.id_product == Product.id
            # )

            query = select(
                Teacher,
                School,
                Product,
                Students
            ).where(
                Teacher.login == login
            ).outerjoin(
                School, Teacher.id_school == School.id
            ).outerjoin(
                Students, Teacher.id_school == Students.id_school
            ).outerjoin(
                Product, Students.id_product == Product.id
            )

            
            result = await session.execute(query)
            teacher = result.all()
            print(teacher)
            
                
            if not teacher:
                return {"status": "not_found", "message": "Учитель не найден"}
            
            
            if not teacher[0].Teacher.check_password(password):
                    return {"status": "not_found", "message": "Неверный логин или пароль"}
            import pprint 
                
            returns_projects = []
            for record in teacher:
                teacher_obj, school_obj, product_obj, student_obj = record
                # Если учётная запись admin, то связанных данных о студентах может не быть
                if teacher_obj.admin:
                    # Формируем имя для админа, можно использовать, например, логин или пустую строку
                    full_name = teacher_obj.login
                else:
                    # Если студент отсутствует, пропускаем запись
                    if student_obj is None:
                        continue
                    full_name = f"{student_obj.surname or ''} {student_obj.name or ''} {student_obj.father_name or ''}".strip()
                
                returns_projects.append({
                    "id": product_obj.id if product_obj else None,
                    "name": full_name,
                    "school_name": school_obj.school_name if school_obj else None,
                    "project_name": product_obj.product_name if product_obj else None,
                    "project_slot": product_obj.location if product_obj else None,
                    "project_format": product_obj.project_format if product_obj else None,
                    "project_datetime_start": product_obj.date_time_start if product_obj else None,
                    "project_datetime_end": product_obj.date_time_end if product_obj else None,
                })

            # teacher = teacher.to_dict()
            pprint.pprint(returns_projects)
            return {
                "status": "success", 
                "projects": returns_projects, 
                "user": {
                    "id": teacher[0].Teacher.id,
                    "login": teacher[0].Teacher.login, 
                    "password": teacher[0].Teacher.password, 
                    "school_name": teacher[0].School.school_name if teacher[0].School else None,
                    "admin": teacher[0].Teacher.admin,
                } 
            }


    # async def get_current_teacher(credentials: HTTPBasicCredentials = Depends(security)):
    #     async with async_session_factory() as session:
    #         # Ищем учителя по логину
    #         query = select(Teacher).where(Teacher.login == credentials.username)
    #         result = await session.execute(query)
    #         teacher = result.scalar_one_or_none()
            
    #         if not teacher:
    #             raise HTTPException(
    #                 status_code=status.HTTP_401_UNAUTHORIZED,
    #                 detail="Неверный логин или пароль",
    #             )
                
    #         # Проверяем пароль
    #         if not teacher.check_password(credentials.password):
    #             raise HTTPException(
    #                 status_code=status.HTTP_401_UNAUTHORIZED,
    #                 detail="Неверный логин или пароль",
    #             )
                
    #         return teacher
            

    @staticmethod
    # @auth_required
    async def select_students_by_school_id(id_school):
        async with async_session_factory() as session:
            # Получаем всех студентов учителя с указанным id учебного заведения
            query = select(Students).where(Students.id_school == id_school)
            result = await session.execute(query)
            students = result.scalars().all()
            
            return {
                "students": [s.to_dict() for s in students],
            }

    @staticmethod
    # @auth_required
    async def select_project_by_id(id_product):
        async with async_session_factory() as session:
            # Получаем всех студентов учителя с указанным id учебного заведения
            query = select(Product).where(Product.id == id_school)
            result = await session.execute(query)
            students = result.scalars().all()
            
            return {
                "students": [s.to_dict() for s in students],
            }
            
    @staticmethod
    async def create_admin(log,password):
        async with async_session_factory() as session:
            new_teacher = Teacher(
                login="ivanov",
                admin=True
            )
            new_teacher.set_password("qwerty123")
            session.add(new_teacher)
            await session.commit()

    @staticmethod
    async def find_student_data_by_id(project_id):
        async with async_session_factory() as session:
            query = select(
                Students,
                School,
                Product,
                Conference
            ).join(
                School, Students.id_school == School.id
            ).join(
                Product, Students.id_product == Product.id
            ).outerjoin(
                Conference, Product.id_conference == Conference.id
            ).where(Product.id == project_id)
            #TODO: catch errors and what if table data with join or outerjoin didnt find?

            result = await session.execute(query)
            # s = [student.to_dict() for student in result.scalars().all()]
            student_data = result.all()
            import pprint
            
            
    
            if student_data:
                returns_data = []
                for student in student_data:
                    print(student.Students.surname)
                    returns_data.append({
                        "id": student.Students.id,
                        "surname": student.Students.surname,
                        "name": student.Students.name,
                        "father_name": student.Students.father_name,
                        "section": student.Product.section,
                        "image_url": student.Product.url_scheme,
                        "school_name": student.School.school_name,
                        "project_name": student.Product.product_name,
                        "school_class": student.Students.grade,
                        "project_slot": student.Product.location,
                        "project_format": student.Product.project_format,
                        "project_datetime_start": student.Product.date_time_start,
                        "project_datetime_end": student.Product.date_time_end
                    })
                    
                return {
                    "status": "success",
                    "data": returns_data
                }
            return {"status": "not_found", "message": "Студент не найден"}

    @staticmethod
    async def get_master_classes():
        from datetime import datetime, date
        from sqlalchemy import func
        async with async_session_factory() as session:
            try:
                today = date.today()
                next_year_date = date(today.year + 1, 1, 1)

                query = select(MasterClass).where(
                    func.date(MasterClass.date_time_start) >= today,
                    func.date(MasterClass.date_time_start) < next_year_date
                )
                
                result = await session.execute(query)
                master_classes = result.scalars().all()
                
                if not master_classes:
                    return []
                mc = [{
                    "id":master_class.id,
                    "title": master_class.name,
                    "link":master_class.url_link,
                    "data":master_class.date_time_start
                    } for master_class in master_classes]
                import pprint
                pprint.pprint(mc)
                return mc
               
                
            except Exception as e:
                print(f"Ошибка: {e}")
                return []



