# 
FROM python:3.11

# 
WORKDIR /ml

# 
COPY ./requirements.txt /ml/requirements.txt

# 
RUN pip install -r /ml/requirements.txt

# 
COPY ./ /ml/

# 
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8007"]