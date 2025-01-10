# 
FROM python:3.11

# 
WORKDIR /backend

# 
COPY ./requirements.txt /backend/requirements.txt

# 
RUN pip install -r /backend/requirements.txt

# 
COPY ./ /backend/app

# 
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]