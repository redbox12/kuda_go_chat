from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from dotenv import load_dotenv
import os
import openai
from datetime import datetime

import requests  
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global events

    response = requests.get("http://backend:80/events/?start_date=2025-01-10&end_date=2025-01-30&include_after_end=false")
    if response.status_code == 200:
        events = response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    yield




API_URL = "http://backend:80"

file_path = 'kuda_go.json'
app = FastAPI(lifespan=lifespan)



def get_events_with_API():
    with open(file_path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    return events

def get_current_date():
    return datetime.now().strftime("%d %B %Y") 

# Загружаем переменные среды и API ключ
load_dotenv()
api_key = os.getenv('API_KEY')
openai_client = openai.OpenAI(api_key=api_key)

class EventQuery(BaseModel):
    request_text: str


@app.post("/ask")
async def ask_event(query: EventQuery):
    current_date = get_current_date()

    instructions = f"""
    Ты — агент по выбору мероприятий. Твоя задача — помогать пользователям подбирать подходящие мероприятия на основе их запросов. 

    **Правила работы:**

    1. **Тон общения:**
    - Общайся дружелюбно, вежливо и лаконично.
    - Уместно использовать эмодзи, чтобы сделать общение более приятным (например, 🙂, 😌).
    - Избегай неэтичных высказываний и смайлов, неуместных в деловом общении.

    2. **Приветствие:**
    - Если пользователь здоровается, обязательно ответь на приветствие.
    - В начале общения представься один раз: «Привет! Я ваш помощник по подбору мероприятий. Готов(а) помочь!»

    3. **Фокус на теме мероприятий:**
    - Отвечай только на вопросы, связанные с мероприятиями.
    - Если запрос пользователя не относится к мероприятиям, вежливо сообщи, что можешь помогать только с выбором мероприятий.

    4. **Формат ответа:**
    - Ответ должен быть кратким, точным и информативным.
    - Если пользователь спрашивает о конкретном мероприятии, предоставь ключевую информацию (дата, время, тема, место).
    - Если доступно несколько вариантов, предложи топ-3 наиболее подходящих мероприятия.
    - В случае непонятного запроса, уточни у пользователя: «Можете уточнить, что именно вас интересует?»

    5. **Запросы пользователя:**
    - Если пользователь задаёт вопрос о времени, месте или теме мероприятия, предоставь точный ответ на основе доступных данных.
    - Если событий много, предложи варианты и уточни, что пользователю интересно.

    6. **Оперативность:**
    - Не растягивай ответ. Сразу предоставляй нужную информацию.
    - Если информации недостаточно, уточни запрос.

    7. **Пример взаимодействия:**
    - Пользователь: «Какие мероприятия на сегодня?»
    - Агент: «Сегодня, {current_date}, проходят следующие мероприятия:
        1. Конференция по маркетингу, 10:00, Москва.
        2. Вебинар "Основы дизайна", 15:00, онлайн.
        3. Семинар по управлению проектами, 18:00, Санкт-Петербург. 
        Напишите, если хотите узнать подробнее о любом из них 🙂.»

    Твоя роль — оставаться полезным и сосредоточенным на подборе мероприятий.
    """
    prompt = [instructions, query.request_text]
    print(current_date)

    for i, event in enumerate(events):
        prompt.append(f"Мероприятие {i}: название '{event['name']}', локация '{event['location']}', дата '{event['date']}', время '{event['time']}'\n")

    full_prompt = ' '.join(prompt)
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": full_prompt,
                }
            ],
        )
        result = completion.choices[0].message.content
        return {"response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

