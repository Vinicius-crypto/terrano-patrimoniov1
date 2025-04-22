FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p /app/uploads/termos
COPY uploads/ uploads/

COPY . .

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=8000

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]
