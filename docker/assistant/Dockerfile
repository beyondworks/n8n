FROM python:3.11-slim

WORKDIR /app

# certifi for SSL CA bundle (optional but recommended)
RUN pip install --no-cache-dir certifi

# Copy only Python source (exclude node_modules, .venv, etc.)
COPY assistant.py server.py config.json ./
COPY core/ ./core/
COPY domains/ ./domains/

# Create data directory for sessions/memory
RUN mkdir -p /app/data/sessions

EXPOSE 8080

CMD ["python3", "server.py"]
