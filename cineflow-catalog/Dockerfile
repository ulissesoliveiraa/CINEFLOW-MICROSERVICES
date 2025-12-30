FROM python:3.11-slim

WORKDIR /app

# Instalar requisitos
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY ./app /app

# Porta interna do contêiner
EXPOSE 8000

# Rodar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]