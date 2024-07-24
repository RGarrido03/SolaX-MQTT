FROM python:3.12
WORKDIR /app

COPY requirements.txt .
COPY solax.py .
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "./solax.py"]
