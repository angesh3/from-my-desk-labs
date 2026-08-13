FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app /app
COPY policies /policies

ENV POLICY_DIR=/policies
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
