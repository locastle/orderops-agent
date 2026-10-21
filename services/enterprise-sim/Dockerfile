FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY packages/shared ./packages/shared
COPY services/enterprise-sim ./services/enterprise-sim

RUN pip install --no-cache-dir -e ./packages/shared \
    && pip install --no-cache-dir -e ./services/enterprise-sim

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
