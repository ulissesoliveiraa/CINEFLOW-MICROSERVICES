
# 🎬 CineFlow – Backend em Microsserviços

O **CineFlow** é um projeto backend que simula uma plataforma de streaming, desenvolvido com foco em **arquitetura de microsserviços**, **comunicação síncrona e assíncrona** e **orquestração com Docker Compose**.
O projeto prioriza arquitetura e integração entre serviços, sem interface gráfica.

---

## 🧠 Arquitetura do Sistema

O sistema é composto por **3 microsserviços** e **1 broker de mensagens**:

| Serviço            | Responsabilidade                                    | Porta        |
| ------------------ | --------------------------------------------------- | ------------ |
| cineflow-user      | Criação e consulta de usuários e consumo de eventos | 8001         |
| cineflow-catalog   | Consulta de filmes via IMDB / MOCK                  | 8002         |
| cineflow-streaming | Orquestração do playback e publicação de eventos    | 8003         |
| RabbitMQ           | Comunicação assíncrona                              | 5673 / 15673 |

---

## 🔄 Comunicação entre Serviços

* **Síncrona (HTTP)**

  * Streaming valida usuário no User Service
  * Streaming valida filme no Catalog Service

* **Assíncrona (RabbitMQ)**

  * Streaming publica evento de playback
  * User Service consome e registra o evento

---

## 🛠 Tecnologias Utilizadas

* Python 3.11
* FastAPI
* Pydantic
* RabbitMQ
* aio-pika
* httpx
* Docker
* Docker Compose
* Swagger / OpenAPI

---

## 📁 Estrutura do Projeto

```
CineFlow/
├── docker-compose.yml
├── .env.example
│
├── cineflow-user/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── cineflow-catalog/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── cineflow-streaming/
│   ├── app/
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
```

---

## 🔐 Variáveis de Ambiente

Por **questões de segurança**, o arquivo `.env` **não é versionado** neste repositório.

Cada usuário deve criar manualmente seu próprio arquivo `.env` na raiz do projeto e informar **sua própria chave da API IMDB (RapidAPI)**.

### Exemplo de `.env` (modelo):

```env
IMDB_API_KEY=YOUR_RAPIDAPI_KEY_HERE
RAPIDAPI_HOST=imdb236.p.rapidapi.com
```

> Caso a chave de API não seja informada ou seja inválida, o **Catalog Service utiliza automaticamente um MOCK**, permitindo que o projeto funcione normalmente para testes e demonstrações.

---

## ▶️ Como Executar o Projeto

### Pré-requisitos

* Docker Desktop instalado e em execução
* Docker Compose v2 ou superior

---

### Passo a passo

1. Clone o repositório:

```bash
git clone https://github.com/Raimundofiles/CineFlow-Microservices.git
```

2. Acesse a pasta do projeto:

```bash
cd CineFlow
```

3. Crie o arquivo `.env` conforme o modelo apresentado acima

4. Suba os containers:

```bash
docker compose up -d
```

5. Verifique se os serviços estão ativos:

```bash
docker compose ps
```

---

### Portas utilizadas

* User Service: [http://localhost:8001](http://localhost:8001)
* Catalog Service: [http://localhost:8002](http://localhost:8002)
* Streaming Service: [http://localhost:8003](http://localhost:8003)
* RabbitMQ (AMQP): 5673
* RabbitMQ (Management): [http://localhost:15673](http://localhost:15673)

---

## 📚 Documentação das APIs (Swagger)

* User Service: [http://localhost:8001/docs](http://localhost:8001/docs)
* Catalog Service: [http://localhost:8002/docs](http://localhost:8002/docs)
* Streaming Service: [http://localhost:8003/docs](http://localhost:8003/docs)

SwaggerHub:

* [https://app.swaggerhub.com/apis/LEOB6471/CineFlowMicroserviceAPI/1.0.0](https://app.swaggerhub.com/apis/LEOB6471/CineFlowMicroserviceAPI/1.0.0)

---

## 🔬 Fluxo de Funcionamento

1. Criar usuário → `POST /users`
2. Consultar filme → `GET /movies/{movie_id}`
3. Iniciar streaming → `POST /playback/start`
4. Evento publicado no RabbitMQ
5. User Service consome o evento e registra no log

---

## 🚧 Possíveis Evoluções

* Persistência com banco de dados
* Autenticação com JWT
* Histórico de playback
* Playlists e recomendações
* Observabilidade (logs, métricas e tracing)
* Orquestração com Kubernetes

---

## 🎯 Objetivo do Projeto

Demonstrar na prática:

* Arquitetura orientada a serviços
* Microsserviços distribuídos
* Comunicação síncrona e assíncrona
* Integração com API externa
* Contêineres e orquestração com Docker Compose



