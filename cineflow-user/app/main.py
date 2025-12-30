from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import os
import asyncio
import aio_pika  # Biblioteca assincrona para RabbitMQ
import json

# --- Configuração de Ambiente e Conexão RabbitMQ ---
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "playback_events"
RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672/"

# --- Modelos de Dados (Schemas)


class UserCreation(BaseModel):
    name: str
    email: str
    active: bool = True


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    active: bool


class PlaybackStart(BaseModel):
    user_id: int
    movie_id: str


# Simulação de um banco de dados em memória
users_db = {}
next_user_id = 1

# --- Instância do FastAPI
app = FastAPI(title="CineFlow User Service", version="1.0.0")

# --- Lógica de Consumo RabbitMQ


async def consume_messages():
    """Conecta ao RabbitMQ e consome a fila de eventos de playback (retry automático)."""
    while True:
        try:
            # connect_robust faz a lógica de retry automaticamente
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            print(" User Service conectado ao RabbitMQ.")

            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue(QUEUE_NAME, durable=True)
                print(
                    f" User Service esperando por mensagens na fila: {QUEUE_NAME}")

                async with queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            # Processa a mensagem
                            event_data = message.body.decode()
                            try:
                                # Aqui você registraria o evento no BD do usuário, etc.
                                print("-" * 50)
                                print(" EVENTO RECEBIDO: Início de Playback!")
                                print(f"Detalhes do Evento: {event_data}")
                                print("-" * 50)
                            except Exception as e:
                                print(
                                    f"X ERRO ao processar mensagem: {e}. Rejeitando mensagem.")
                                # Re-enfileira a mensagem em caso de erro
                                await message.reject(requeue=True)

        except ConnectionRefusedError:
            print(
                f"ERRO: Não foi possível conectar ao RabbitMQ em {RABBITMQ_HOST}. Tentando novamente em 5s...")
            await asyncio.sleep(5)
        except Exception as e:
            print(
                f"X ERRO fatal na conexão RabbitMQ: {e}. Reconectando em 5s...")
            await asyncio.sleep(5)

# Executa o consumidor em segundo plano ao iniciar o FastAPI


@app.on_event("startup")
async def startup_event():
    """Cria a tarefa do consumidor RabbitMQ ao iniciar o serviço."""
    asyncio.create_task(consume_messages())

# --- Rotas REST


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de health check."""
    return {"status": "User Service Healthy"}


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Usuários"])
def create_user(user: UserCreation):
    """Cria um novo usuário e o armazena na memória."""
    global next_user_id

    if any(u.get("email") == user.email for u in users_db.values()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    user_id = next_user_id
    user_data = user.model_dump()  # Usar model_dump() para Pydantic v2+
    user_data["id"] = user_id
    users_db[user_id] = user_data
    next_user_id += 1

    return users_db[user_id]


@app.get("/users/{user_id}", response_model=UserResponse, tags=["Usuários"])
def get_user(user_id: int):
    """Consulta um usuário existente para verificação."""
    user = users_db.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Usuário não encontrado.")
    return user
