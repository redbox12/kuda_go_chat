import datetime
import hashlib
import json
import os
import sqlite3
from typing import Optional
from typing import List
import jwt
from fastapi import FastAPI, Query
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import requests

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
KUDAGO_API_URL = "https://kudago.com/public-api/v1.4/events/"

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app = FastAPI()


class User(BaseModel):
    name: str
    email: EmailStr
    password: str

    def hash_password(self):
        return hashlib.sha256(self.password.encode()).hexdigest()


class LoginUser(BaseModel):
    email: EmailStr
    password: str

    def hash_password(self):
        return hashlib.sha256(self.password.encode()).hexdigest()


class EchoData(BaseModel):
    message: str


def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()


init_db()


def add_user_to_db(user: User):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (user.name, user.email, user.hash_password())
    )
    conn.commit()
    conn.close()


def get_user_by_email(email: str):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=credentials_exception)
        user = get_user_by_email(email)
        if user is None:
            raise HTTPException(status_code=credentials_exception)
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=credentials_exception)

def is_file_empty(file_path):
    """Проверяет, пуст ли файл по его размеру."""
    return os.path.getsize(file_path) == 0

@app.post("/register")
async def register(user: User):
    existing_user = get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    add_user_to_db(user)
    return {"status": 200,"message": "User registered successfully"}


@app.post("/login")
async def login(user: LoginUser):
    # existing_user: 1 - name, 2 - email, 3 - password
    existing_user = get_user_by_email(user.email)
    if not existing_user:
        raise HTTPException(status_code=400, detail="User not found")

    stored_password = existing_user[3]
    if stored_password != user.hash_password():
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": existing_user[2]}, expires_delta=access_token_expires
    )

    return {"message": "Login successful", "user": {"name": existing_user[1], "email": existing_user[2]},
            "access_token": access_token,
            "token_type": "bearer",
            "status": 200}


@app.get("/events/", response_model=List[dict])
def get_events(
    start_date: str = Query(..., description="Start date in format YYYY-MM-DD"),
    end_date: str = Query(..., description="End date in format YYYY-MM-DD"),
    include_after_end: bool = Query(False, description="Include events after end_date")
):
    """
    Get events from Kudago API for a specific date range.
    """
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}

    if start > end:
        return {"error": "Start date must be earlier than end date."}

    # Convert dates to timestamps for Kudago API
    start_timestamp = int(start.timestamp())
    end_timestamp = int(end.timestamp())

    params = {
        "actual_since": start_timestamp,
        "actual_until": end_timestamp,
        "location": "msk",
        "fields": "id,title,place,dates,short_title,categories",
        "expand": "place,dates",
        "page_size": 100
    }

    response = requests.get(KUDAGO_API_URL, params=params)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data from Kudago API. Status code: {response.status_code}"}

    data = response.json()
    events = []

    for item in data.get("results", []):
        try:
            event_id = item.get("id")
            name = item.get("title") or item.get("short_title")
            location = item.get("place", {}).get("address", "Unknown location")
            dates = item.get("dates", [])

            # Обработка категории
            event_type = item.get("categories")
            if event_type and isinstance(event_type, list):
                event_type = event_type[0].capitalize()
            else:
                event_type = "Unknown"

            for date_info in dates:
                start_timestamp = date_info.get("start")

                # Пропустить, если нет даты начала
                if not start_timestamp:
                    continue

                event_start_datetime = datetime.datetime.fromtimestamp(start_timestamp)

                # Строгая проверка диапазона дат
                if not include_after_end:
                    if event_start_datetime < start or event_start_datetime > end:
                        continue
                else:
                    # Если include_after_end=True, показываем события начиная с start_date без ограничения по end_date
                    if event_start_datetime < start:
                        continue

                event_date = event_start_datetime.strftime("%Y-%m-%d")
                event_time = event_start_datetime.strftime("%H:%M")

                events.append({
                    "id": event_id,
                    "type": event_type,
                    "name": name,
                    "location": location,
                    "date": event_date,
                    "time": event_time
                })
        except Exception as e:
            print(f"Error parsing event: {e}")

    # Сортировка событий по дате и времени
    events.sort(key=lambda x: (x["date"], x["time"]))
    return events
