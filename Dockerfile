FROM python:3.14-slim

RUN adduser --disabled-password --no-create-home appuser

WORKDIR /app

COPY agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent/

USER appuser

EXPOSE 8080

CMD ["uvicorn", "agent.agent_api:app", "--host", "0.0.0.0", "--port", "8080"]
