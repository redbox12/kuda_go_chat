# Frontend Dockerfile
FROM python:3.9-slim

# Устанавливаем зависимости
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Копируем исходный код
COPY . /app

# Запускаем Streamlit
CMD ["streamlit", "run", "chatbot_app.py", "--server.port=8501", "--server.address=0.0.0.0"]