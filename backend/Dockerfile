FROM python:3.12-slim
WORKDIR /app
RUN pip install poetry
COPY . .
RUN poetry install
EXPOSE 8000
CMD ["poetry", "run", "fastapi", "run", "backend/main.py"]
#CMD ["uvicorn", "fastapi:app", "--host", "0.0.0.0", "--port", "8000"]