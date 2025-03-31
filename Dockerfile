FROM python:3.9-slim

WORKDIR /app

COPY requirements/prod.txt .

RUN pip install --no-cache-dir -r prod.txt

COPY . .

CMD ["python", "bot.py"]  # Заменить на название интерфейса 