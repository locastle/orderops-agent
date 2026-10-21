FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# The shared vocabulary is installed first: the service declares it as a
# dependency, so pip can satisfy it from the local package instead of PyPI.
COPY packages/shared ./packages/shared
COPY services/ai-api ./services/ai-api

RUN pip install --no-cache-dir -e ./packages/shared \
    && pip install --no-cache-dir -e ./services/ai-api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
