FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY src ./src

RUN useradd --create-home --uid 10001 app
USER app

ENTRYPOINT ["python", "-m", "taskboard"]
