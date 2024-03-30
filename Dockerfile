# Use an official Python runtime as a parent image
FROM python:3.11.8-slim

LABEL python_version="3.11.8"

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the container
EXPOSE 8000

CMD ["uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
