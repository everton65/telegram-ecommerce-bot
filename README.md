# Bot de Vendas — Telegram

Bot de e-commerce simples para Telegram usando Python e PostgreSQL.

## Comandos
- `/start` — Boas-vindas e menu
- `/produtos` — Lista produtos disponíveis
- `/pedido <id>` — Faz um pedido
- `/status` — Consulta o último pedido

## Como rodar

### 1. Clone o repositório
```bash
git clone <url-do-repo>
cd bot_telegram
```

### 2. Configure o ambiente
```bash
cp .env.example .env
# Edite o .env com seu token e senha do banco
```

### 3. Suba o banco
```bash
docker-compose up -d
```

### 4. Instale dependências
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Rode o bot
```bash
python main.py
```
