FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY . /app

RUN python -m wcmodel.cli generate --sims 5000 --seed 2026

EXPOSE 8080
CMD ["python", "-m", "wcmodel.cli", "serve", "--host", "0.0.0.0", "--port", "8080"]
