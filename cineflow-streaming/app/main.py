from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import httpx
import os
import aio_pika  # Produtor de mensagens assincrono

# --- Configuração de Ambiente
# URLs para chamadas HTTP sincronas (usando nomes de serviço Docker + porta interna 8000)
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://cineflow-user:8000")
CATALOG_SERVICE_URL = os.getenv(
    "CATALOG_SERVICE_URL", "http://cineflow-catalog:8000")

# Configuração RabbitMQ (Publicador)
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
QUEUE_NAME = "playback_events"
RABBITMQ_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASS}@{RABBITMQ_HOST}:5672/"

# --- Modelos de Dados (Schemas)


class PlaybackStart (BaseModel):
    user_id: int
    movie_id: str


# --- Instância do FastAPI
app = FastAPI(title="CineFlow Streaming Service", version="1.0.0")

# Armazenamento da conexão RabbitMQ globalmente
rabbitmq_connection = None


@app.on_event("startup")
async def connect_to_rabbitmq():
    """Estabelece a conexão robusta com o RabbitMQ ao iniciar."""
    global rabbitmq_connection
    try:
        # connect_robust cuida da reconexão
        rabbitmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
        print(" Streaming Service conectado ao RabbitMQ.")
    except Exception as e:
        print(f"X ERRO ao conectar ao RabbitMQ: {e}")
        # O serviço ainda pode tentar rodar, mas a rota de POST falhará.


@app.on_event("shutdown")
async def disconnect_from_rabbitmq():
    """Fecha a conexão com o RabbitMQ ao desligar."""
    global rabbitmq_connection
    if rabbitmq_connection:
        await rabbitmq_connection.close()
        print(" Streaming Service desconectado do RabbitMQ.")

# --- Rotas REST


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de health check."""
    return {"status": "Streaming Service Healthy"}


@app.post("/playback/start", tags=["Streaming"])
async def start_playback(data: PlaybackStart):
    """
    1. Verifica usuário e filme (HTTP Sincrono).
    2. Publica evento de playback (RabbitMQ Assincrono).
    """

    # 1. Verificações Síncronas (HTTP)
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1A. Verificação Sincrona do Usuário
        try:
            user_url = f"{USER_SERVICE_URL}/users/{data.user_id}"
            user_response = await client.get(user_url)
            user_response.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Usuário ID {data.user_id} não encontrado.")
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço User indisponível.")

        # 1B. Verificação Sincrona do Filme
        try:
            movie_url = f"{CATALOG_SERVICE_URL}/movies/{data.movie_id}"
            movie_response = await client.get(movie_url)
            movie_response.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Filme ID {data.movie_id} não encontrado no catálogo.")
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Serviço Catalog indisponível.")

    # 2. Publicação Assincrona no RabbitMQ
    global rabbitmq_connection
    if not rabbitmq_connection or rabbitmq_connection.is_closed:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Falha na conexão com o RabbitMQ.")

    try:
        channel = await rabbitmq_connection.channel()
        # Garante que a fila existe
        await channel.declare_queue(QUEUE_NAME, durable=True)

        # Serializa o objeto Pydantic para JSON
        message_body = data.model_dump_json()  # Use model_dump_json() para Pydantic v2+

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=message_body.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=QUEUE_NAME,
        )
        print(
            f" Evento de Playback publicado para Usuário: {data.user_id}, Filme: {data.movie_id}")

    except Exception as e:
        print(f"X ERRO ao publicar mensagem no RabbitMQ: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Falha ao publicar evento de streaming.")

    return {"message": "Streaming iniciado e evento de playback publicado."}
