FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput --settings=inventory_platform.settings

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "inventory_platform.wsgi:application", "--bind", "0.0.0.0:8000"]