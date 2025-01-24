
# Ассистент по поиску досуга

Чат-бот для ассистента, который в диалоговой форме предлагает места для посещения.

## Чат-бот
![Чат-бот](/img/example_programm.jpg)

## Инструкция по запуску

1. Создайте файл .env с содержимым, где надо указать API ключ от OpenAI:
```
API_KEY=1231jlkj 
```
2. Установить docker
3. Запуск программы:
```bash
 docker-compose up --build
```


## Программа
- Чат досуга: http://localhost:8501/
- Swagger Backend: http://localhost:80/docs/
- Swagger ML server: http://localhost:8007/docs/


## Тeхнологии
- FastAPI
- Streamlit
- Sqlite
- OpenAI
- Docker

