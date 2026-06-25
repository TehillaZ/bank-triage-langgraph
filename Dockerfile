FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --upgrade pip \
    && python -m pip install pytest python-dotenv pydantic langgraph langchain-groq

COPY . .

ENTRYPOINT ["python", "main.py"]
