FROM python:3.12-slim
WORKDIR /app
COPY login_app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["uvicorn", "login_app.main:app", "--host", "0.0.0.0", "--port", "3000"]