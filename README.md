# 🛒 Loja Santos Bot — Telegram

Bot de e-commerce desenvolvido em Python para a plataforma Telegram como projeto de extensão acadêmico. Permite que clientes visualizem produtos, realizem pedidos, acompanhem o histórico e finalizem a compra via WhatsApp, tudo dentro do chat.

---

## 👥 Equipe

| Integrante | Responsabilidade |
|---|---|
| Everton Juan | Fase 1 — Configuração inicial, ambiente e banco de dados |
| Luan Felipe | Fase 2 — Desenvolvimento dos comandos do bot |
| Otávio Vinicius | Fase 3 — Testes, ajustes e validação |

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|---|---|---|
| Python | 3.11+ | Linguagem principal |
| python-telegram-bot | 20.7 | Integração com a API do Telegram |
| PostgreSQL | 15 | Banco de dados relacional |
| psycopg2-binary | 2.9.9 | Conexão Python ↔ PostgreSQL |
| Docker | — | Containerização do banco de dados |
| python-dotenv | 1.0.0 | Gerenciamento de variáveis de ambiente |

---

## 💬 Comandos disponíveis

| Comando | Descrição |
|---|---|
| `/start` | Boas-vindas com menu de botões interativos |
| `/produtos` | Lista o catálogo completo com preços e IDs |
| `/produto <id>` | Registra um pedido e gera link para finalizar no WhatsApp |
| `/status` | Exibe histórico de pedidos com opção de finalizar no WhatsApp |
| `/buscar <nome>` | Busca produtos por nome ou descrição |
| `/promocoes` | Lista as promoções cadastradas com links externos |
| `/ranking` | Exibe os produtos mais vendidos |
| `/admin` | Painel administrativo com métricas da loja |
| `/ajuda` | Lista todos os comandos disponíveis |

> Todos os comandos também estão disponíveis via **botões inline**, sem necessidade de digitar.

---

## 📁 Estrutura do projeto

```
telegram-ecommerce-bot/
├── main.py                  # Inicialização e registro dos handlers
├── requirements.txt         # Dependências do projeto
├── docker-compose.yml       # Configuração do PostgreSQL via Docker
├── .env.example             # Modelo de variáveis de ambiente
├── .gitignore               # Arquivos ignorados pelo Git
├── bot/
│   ├── __init__.py
│   └── handlers.py          # Lógica de todos os comandos e callbacks
└── db/
    ├── __init__.py
    ├── connection.py         # Context manager de conexão com o banco
    ├── schema.sql            # Criação das 4 tabelas
    └── seed.sql              # 10 produtos e 5 promoções de exemplo
```

---

## ⚙️ Como configurar e rodar

### Pré-requisitos

- Python 3.11 ou superior
- Docker Desktop instalado e rodando
- Token do bot gerado via [@BotFather](https://t.me/BotFather)

### 1. Clone o repositório

```bash
git clone https://github.com/everton65/telegram-ecommerce-bot.git
cd telegram-ecommerce-bot
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` com suas credenciais:

```env
BOT_TOKEN=seu_token_aqui
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bot_vendas
DB_USER=postgres
DB_PASSWORD=sua_senha_aqui
```

> ⚠️ Nunca suba o `.env` para o repositório. Ele já está listado no `.gitignore`.

### 3. Suba o banco de dados

```bash
docker-compose up -d
```

O Docker criará automaticamente o banco, as tabelas e os dados iniciais.

### 4. Crie o ambiente virtual e instale as dependências

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 5. Rode o bot

```bash
python main.py
```

Se tudo estiver correto, o terminal exibirá:

```
Bot rodando...
```

---

## 🗄️ Banco de dados

### Tabelas

**usuarios** — cadastrado automaticamente no primeiro `/start`.

| Coluna | Tipo | Descrição |
|---|---|---|
| id | BIGINT | ID do Telegram (PK) |
| nome | VARCHAR | Primeiro nome |
| criado_em | TIMESTAMP | Data de cadastro |

**produtos** — catálogo da loja.

| Coluna | Tipo | Descrição |
|---|---|---|
| id | SERIAL | ID do produto (PK) |
| nome | VARCHAR | Nome do produto |
| descricao | TEXT | Descrição breve |
| preco | NUMERIC | Preço em reais |
| disponivel | BOOLEAN | Se aparece no catálogo |

**pedidos** — histórico de compras.

| Coluna | Tipo | Descrição |
|---|---|---|
| id | SERIAL | ID do pedido (PK) |
| usuario_id | BIGINT | FK → usuarios |
| produto_id | INT | FK → produtos |
| status | VARCHAR | pendente / confirmado / enviado / entregue / cancelado |
| criado_em | TIMESTAMP | Data e hora |

**promocoes** — ofertas externas exibidas no `/promocoes`.

| Coluna | Tipo | Descrição |
|---|---|---|
| id | SERIAL | ID da promoção (PK) |
| produto | VARCHAR | Nome do produto em promoção |
| preco | NUMERIC | Preço promocional |
| loja | VARCHAR | Nome da loja |
| link | TEXT | Link externo da oferta |
| criado_em | TIMESTAMP | Data de cadastro |

### Dados iniciais (seed)

**10 produtos:** Camiseta Básica, Calça Jeans, Tênis Casual, Boné Aba Curva, Mochila Urbana, Relógio, Cinto de Couro, Bermuda, Corta Vento, Moletom com Capuz.

**5 promoções:** SSD Kingston 1TB, Mouse Gamer Redragon, Headset HyperX Cloud, Teclado Mecânico Redragon, Monitor 24" Full HD.

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais.