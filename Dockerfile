# EXPLICACIÓN: Multi-stage build para imagen ligera y segura
FROM python:3.12-slim as builder

# EXPLICACIÓN: Instalar dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# EXPLICACIÓN: Copiar requirements primero para aprovechar cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# EXPLICACIÓN: Fase final con imagen minimalista
FROM python:3.12-slim

WORKDIR /app

# EXPLICACIÓN: Copiar paquetes instalados del builder
COPY --from=builder /install /usr/local

# EXPLICACIÓN: Copiar código de la aplicación
COPY . .

# EXPLICACIÓN: Puerto expuesto por uvicorn
EXPOSE 8000

# EXPLICACIÓN: Comando para ejecutar la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
