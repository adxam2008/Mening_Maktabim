from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

app = FastAPI(title="Mening Maktabim API")

# CORS sozlamalari
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Parol shifrlash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT sozlamalari
SECRET_KEY = "mening-maktabim-secret-key-2024"
ALGORITHM = "HS256"

# Ma'lumotlar bazasi
db = {
    "users": [],
    "teachers": [],
    "students": [],
    "schedule": []
}

# Pydantic modellar
class User(BaseModel):
    id: Optional[int] = None
    username: str
    password: str
    role: str  # admin, teacher, parent
    related_id: Optional[int] = None  # teacher_id yoki student_id

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class Teacher(BaseModel):
    id: Optional[int] = None
    ism: str
    familiya: str
    fan: str
    telefon: str
    email: Optional[str] = None

class Student(BaseModel):
    id: Optional[int] = None
    ism: str
    familiya: str
    sinf: int
    yosh: int
    ota_onasi: str
    telefon: str

class Schedule(BaseModel):
    id: Optional[int] = None
    sinf: int
    kun: str
    vaqt: str
    fan: str
    teacher_id: int
    xona: str

# Parol funksiyalari
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Boshlang'ich ma'lumotlar
def init_data():
    if not db["users"]:
        db["users"] = [
            {
                "id": 1,
                "username": "admin",
                "password": hash_password("admin123"),
                "role": "admin",
                "related_id": None
            },
            {
                "id": 2,
                "username": "aziza",
                "password": hash_password("123456"),
                "role": "teacher",
                "related_id": 1
            },
            {
                "id": 3,
                "username": "ota1",
                "password": hash_password("123456"),
                "role": "parent",
                "related_id": 1
            }
        ]
    
    if not db["teachers"]:
        db["teachers"] = [
            {"id": 1, "ism": "Aziza", "familiya": "Karimova", "fan": "Matematika", "telefon": "+998901234567", "email": "aziza@maktab.uz"},
            {"id": 2, "ism": "Jasur", "familiya": "Toshmatov", "fan": "Fizika", "telefon": "+998901234568", "email": "jasur@maktab.uz"},
            {"id": 3, "ism": "Nodira", "familiya": "Ahmadova", "fan": "Ona tili", "telefon": "+998901234569", "email": "nodira@maktab.uz"},
            {"id": 4, "ism": "Sardor", "familiya": "Rahimov", "fan": "Ingliz tili", "telefon": "+998901234570", "email": "sardor@maktab.uz"},
        ]
    
    if not db["students"]:
        db["students"] = [
            {"id": 1, "ism": "Akmal", "familiya": "Usmonov", "sinf": 5, "yosh": 11, "ota_onasi": "Usmanov Abbos", "telefon": "+998901111111"},
            {"id": 2, "ism": "Malika", "familiya": "Yusupova", "sinf": 5, "yosh": 11, "ota_onasi": "Yusupov Mansur", "telefon": "+998901111112"},
            {"id": 3, "ism": "Dilshod", "familiya": "Karimov", "sinf": 7, "yosh": 13, "ota_onasi": "Karimov Davron", "telefon": "+998901111113"},
            {"id": 4, "ism": "Nilufar", "familiya": "Aliyeva", "sinf": 9, "yosh": 15, "ota_onasi": "Aliyev Olim", "telefon": "+998901111114"},
            {"id": 5, "ism": "Javohir", "familiya": "Ergashev", "sinf": 11, "yosh": 17, "ota_onasi": "Ergashev Shavkat", "telefon": "+998901111115"},
        ]
    
    if not db["schedule"]:
        db["schedule"] = [
            {"id": 1, "sinf": 5, "kun": "Dushanba", "vaqt": "08:00-08:45", "fan": "Matematika", "teacher_id": 1, "xona": "201"},
            {"id": 2, "sinf": 5, "kun": "Dushanba", "vaqt": "09:00-09:45", "fan": "Ona tili", "teacher_id": 3, "xona": "105"},
            {"id": 3, "sinf": 7, "kun": "Dushanba", "vaqt": "08:00-08:45", "fan": "Fizika", "teacher_id": 2, "xona": "302"},
            {"id": 4, "sinf": 9, "kun": "Seshanba", "vaqt": "10:00-10:45", "fan": "Ingliz tili", "teacher_id": 4, "xona": "108"},
        ]

init_data()

# LOGIN
@app.post("/api/login", response_model=Token)
def login(user_login: UserLogin):
    user = next((u for u in db["users"] if u["username"] == user_login.username), None)
    
    if not user or not verify_password(user_login.password, user["password"]):
        raise HTTPException(status_code=401, detail="Login yoki parol noto'g'ri")
    
    access_token = create_access_token({"sub": user["username"], "role": user["role"], "id": user["id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user["role"],
        "username": user["username"]
    }

# REGISTER (faqat admin)
@app.post("/api/register")
def register(user: User):
    # Tekshirish
    if any(u["username"] == user.username for u in db["users"]):
        raise HTTPException(status_code=400, detail="Bunday foydalanuvchi mavjud")
    
    user_id = max([u["id"] for u in db["users"]], default=0) + 1
    new_user = {
        "id": user_id,
        "username": user.username,
        "password": hash_password(user.password),
        "role": user.role,
        "related_id": user.related_id
    }
    db["users"].append(new_user)
    return {"message": "Foydalanuvchi qo'shildi"}

# TEACHERS
@app.get("/api/teachers", response_model=List[Teacher])
def get_teachers():
    return db["teachers"]

@app.get("/api/teachers/{teacher_id}", response_model=Teacher)
def get_teacher(teacher_id: int):
    teacher = next((t for t in db["teachers"] if t["id"] == teacher_id), None)
    if not teacher:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    return teacher

@app.post("/api/teachers", response_model=Teacher)
def create_teacher(teacher: Teacher):
    teacher_id = max([t["id"] for t in db["teachers"]], default=0) + 1
    teacher_dict = teacher.dict()
    teacher_dict["id"] = teacher_id
    db["teachers"].append(teacher_dict)
    return teacher_dict

@app.put("/api/teachers/{teacher_id}", response_model=Teacher)
def update_teacher(teacher_id: int, teacher: Teacher):
    idx = next((i for i, t in enumerate(db["teachers"]) if t["id"] == teacher_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    teacher_dict = teacher.dict()
    teacher_dict["id"] = teacher_id
    db["teachers"][idx] = teacher_dict
    return teacher_dict

@app.delete("/api/teachers/{teacher_id}")
def delete_teacher(teacher_id: int):
    idx = next((i for i, t in enumerate(db["teachers"]) if t["id"] == teacher_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="O'qituvchi topilmadi")
    db["teachers"].pop(idx)
    return {"message": "O'qituvchi o'chirildi"}

# STUDENTS
@app.get("/api/students", response_model=List[Student])
def get_students(sinf: Optional[int] = None):
    if sinf:
        return [s for s in db["students"] if s["sinf"] == sinf]
    return db["students"]

@app.get("/api/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    student = next((s for s in db["students"] if s["id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    return student

@app.post("/api/students", response_model=Student)
def create_student(student: Student):
    student_id = max([s["id"] for s in db["students"]], default=0) + 1
    student_dict = student.dict()
    student_dict["id"] = student_id
    db["students"].append(student_dict)
    return student_dict

@app.put("/api/students/{student_id}", response_model=Student)
def update_student(student_id: int, student: Student):
    idx = next((i for i, s in enumerate(db["students"]) if s["id"] == student_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    student_dict = student.dict()
    student_dict["id"] = student_id
    db["students"][idx] = student_dict
    return student_dict

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int):
    idx = next((i for i, s in enumerate(db["students"]) if s["id"] == student_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi")
    db["students"].pop(idx)
    return {"message": "O'quvchi o'chirildi"}

# SCHEDULE
@app.get("/api/schedule", response_model=List[Schedule])
def get_schedule(sinf: Optional[int] = None, teacher_id: Optional[int] = None):
    result = db["schedule"]
    if sinf:
        result = [s for s in result if s["sinf"] == sinf]
    if teacher_id:
        result = [s for s in result if s["teacher_id"] == teacher_id]
    return result

@app.get("/api/schedule/{schedule_id}", response_model=Schedule)
def get_schedule_item(schedule_id: int):
    schedule = next((s for s in db["schedule"] if s["id"] == schedule_id), None)
    if not schedule:
        raise HTTPException(status_code=404, detail="Dars topilmadi")
    return schedule

@app.post("/api/schedule", response_model=Schedule)
def create_schedule(schedule: Schedule):
    schedule_id = max([s["id"] for s in db["schedule"]], default=0) + 1
    schedule_dict = schedule.dict()
    schedule_dict["id"] = schedule_id
    db["schedule"].append(schedule_dict)
    return schedule_dict

@app.put("/api/schedule/{schedule_id}", response_model=Schedule)
def update_schedule(schedule_id: int, schedule: Schedule):
    idx = next((i for i, s in enumerate(db["schedule"]) if s["id"] == schedule_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Dars topilmadi")
    schedule_dict = schedule.dict()
    schedule_dict["id"] = schedule_id
    db["schedule"][idx] = schedule_dict
    return schedule_dict

@app.delete("/api/schedule/{schedule_id}")
def delete_schedule(schedule_id: int):
    idx = next((i for i, s in enumerate(db["schedule"]) if s["id"] == schedule_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Dars topilmadi")
    db["schedule"].pop(idx)
    return {"message": "Dars o'chirildi"}

# STATISTIKA
@app.get("/api/stats")
def get_stats():
    return {
        "jami_oquvchilar": len(db["students"]),
        "jami_oqituvchilar": len(db["teachers"]),
        "jami_darslar": len(db["schedule"]),
        "sinflar": {
            str(i): len([s for s in db["students"] if s["sinf"] == i])
            for i in range(1, 12)
        }
    }

@app.get("/")
def root():
    return {
        "message": "Mening Maktabim API - Login tizimi bilan",
        "version": "2.0",
        "docs": "/docs",
        "default_users": {
            "admin": {"username": "admin", "password": "admin123"},
            "teacher": {"username": "aziza", "password": "123456"},
            "parent": {"username": "ota1", "password": "123456"}
        }
    }

# Serverni ishga tushirish uchun:
# pip install pyjwt passlib bcrypt
# uvicorn main:app --reload