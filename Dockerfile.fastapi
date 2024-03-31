FROM python:3.11.8-slim

LABEL python_version="3.11.8"

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
