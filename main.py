import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI,Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
from excel_processor import start_parse_excel

current_file_path = os.path.abspath(__file__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(current_file_path))
sys.path.insert(0, PROJECT_ROOT)
# sys.path.insert(1, os.path.join(sys.path[0], '..'))

from db.queries.orm import AsyncORM
from pydantic import BaseModel

class StudentAuthRequest(BaseModel):
    first_name: str
    second_name: str

class StudentInfoReq(BaseModel):
    project_id: int

class TeacherAuthRequest(BaseModel):
    login: str
    password: str

class StudentFindReq(BaseModel):
    id_school: int

def create_fastapi_app():
    app = FastAPI(title="FastAPI")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
        
        
    @app.get("/students")
    async def get_stud():
        students = await AsyncORM.select_students()
        return students
    
    @app.post("/students_by_school_id")
    async def get_stud(request: StudentFindReq):
        students = await AsyncORM.select_students_by_school_id(**request.dict())
        return students

    @app.get("/workshops")
    async def get_mc():
        mc = await AsyncORM.get_master_classes()
        return mc

    # @app.get("/students")
    # async def auth_teacher(request: TeacherAuthRequest):
    #     return await AsyncORM.select_students_by_teacher_id(teacher)
    
    @app.post("/teacher/auth")
    async def auth_student(request: TeacherAuthRequest):
        result = await AsyncORM.auth_teacher(**request.dict())
        
        if result.get("status") == "not_found":
            raise HTTPException(
                status_code=401,
                detail="Учитель не найден",
                headers={"X-Error": "Teacher not found"}
            )
            
        return result
    
    @app.post("/speaker/search")
    async def auth_student(request: StudentAuthRequest):
        result = await AsyncORM.auth_student(**request.dict())
        
        if result.get("status") == "not_found":
            raise HTTPException(
                status_code=401,
                detail="Студент не найден",
                headers={"X-Error": "Student not found"}
            )
        
        return result

    @app.get("/speaker/{project_id}")
    async def get_student_info(project_id):
        return await AsyncORM.find_student_data_by_id(int(project_id))
    
    return app
    

app = create_fastapi_app()

async def main():
    try:
        await AsyncORM.create_tables()
        await AsyncORM.insert_students()
        await AsyncORM.select_students()
        logging.info("SUCCESS!!!")
        print("БД раскатана!")
        await start_parse_excel()
    except Exception as e:
        print(f"Ошибка при раскатке БД: {str(e)}")
        sys.exit(1)
    


if __name__ == "__main__":
    if "--webserver" in sys.argv:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("app.log"),
                logging.StreamHandler()
            ]
        )
        uvicorn.run(
            app="main:app",  # Используем текущий файл
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        asyncio.run(main())