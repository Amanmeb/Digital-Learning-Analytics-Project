FROM python:3.12-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --default-timeout=1000 --retries 10 --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
