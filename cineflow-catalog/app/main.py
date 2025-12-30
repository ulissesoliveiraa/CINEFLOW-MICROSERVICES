from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import httpx
import os
import json  # Não é estritamente necessário para este código, mas útil para debug

# --- Configuração de Ambiente
IMDB_API_KEY = os.getenv("IMDB_API_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "imdb236.p.rapidapi.com")
# A URL base será construída na rota, usando o host configurado

# --- Modelos de Dados (Schemas)


class MovieDetail(BaseModel):
    # Modelo para a resposta do catálogo
    imdb_id: str = Field(..., example="tt0110912")
    title: str = Field(..., example="Pulp Fiction")
    year: int = Field(..., example=1994)


# --- Instância do FastAPI
app = FastAPI(title="CineFlow Catalog Service", version="1.0.0")

# Cliente HTTP assíncrono global
client = httpx.AsyncClient()


@app.on_event("startup")
async def startup_event():
    """Verifica se a chave de API está presente e inicia o cliente HTTP."""
    global client
    # Garante que o cliente HTTP está pronto para uso
    client = httpx.AsyncClient()

    if not IMDB_API_KEY:
        print("X ERRO: IMDB_API_KEY não está configurada. A API IMDB usará MOCK.")
    else:
        print(" Chave IMDB API configurada e cliente HTTP pronto.")


@app.on_event("shutdown")
async def shutdown_event():
    """Fecha o cliente HTTP ao desligar."""
    await client.aclose()

# --- Rotas REST


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de health check."""
    return {"status": "Catalog Service Healthy"}


@app.get("/movies/{movie_id}", response_model=MovieDetail, tags=["Catálogo"])
async def get_movie(movie_id: str):
    """Consulta detalhes de um filme via RapidAPI, com MOCK fallback em caso de falha de chave/assinatura."""

    # 1. Tenta a chamada à API externa
    # Verifica se a chave foi fornecida e tenta a chamada real
    if IMDB_API_KEY and IMDB_API_KEY != "[SUA NOVA CHAVE IMDB ATIVA AQUI]":
        url = f"https://{RAPIDAPI_HOST}/api/imdb/title/{movie_id}"
        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": IMDB_API_KEY
        }

        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()  # Lança erro para 4xx/5xx

            data = response.json()

            # Retorno da API real
            movie_data = {
                "imdb_id": movie_id,
                "title": data.get("title", "Título Desconhecido API"),
                "year": data.get("year", 0)
            }
            return MovieDetail(**movie_data)

        except httpx.HTTPStatusError as e:
            # Captura erros comuns de API Key (403, 404) e faz o MOCK
            print(
                f"ATENÇÃO: Falha na API IMDB (Status {e.response.status_code}): Chave/Assinatura Inválida. Retornando Mock.")
            if e.response.status_code not in [403, 404]:
                # Re-lança outros erros HTTP (ex: 500 interno da RapidAPI)
                raise HTTPException(status_code=e.response.status_code,
                                    detail=f"Erro não esperado na API IMDB: {e.response.text}")

        except httpx.RequestError:
            # Captura erros de conexão/timeout e faz o MOCK
            print("ATENÇÃO: Erro de conexão/timeout com o serviço IMDB. Retornando Mock.")

    # --- MOCK DA RESPOSTA (Ativado se a chave falhar, for rejeitada, ou se estiver ausente) ---
    print("MOCK ATIVADO: Retornando dados simulados.")
    if movie_id == "tt0110912":
        mock_title = "Pulp Fiction (MOCK SUCESSO)"
        mock_year = 1994
    else:
        mock_title = f"Filme ID {movie_id} (MOCK SUCESSO)"
        mock_year = 2024

    return MovieDetail(imdb_id=movie_id, title=mock_title, year=mock_year)
