from telegram import Update
from telegram.ext import ContextTypes
from db.connection import get_connection

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO usuarios (id, nome) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
        (usuario.id, usuario.first_name)
    )
    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
        f"Olá, {usuario.first_name}! Bem-vindo ao Bot de Vendas!\n\n"
        "/produtos — Ver produtos disponíveis\n"
        "/pedido <id> — Fazer um pedido\n"
        "/status — Ver status do seu pedido"
    )

# /produtos
async def produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nome, descricao, preco FROM produtos WHERE disponivel = TRUE")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        await update.message.reply_text("Nenhum produto disponível no momento.")
        return

    msg = "🛍️ *Produtos disponíveis:*\n\n"
    for row in rows:
        msg += f"*#{row[0]} — {row[1]}*\n{row[2]}\nR$ {row[3]:.2f}\n\n"
    msg += "Para pedir: `/pedido <número do produto>`"

    await update.message.reply_text(msg, parse_mode="Markdown")

# /pedido
async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("Use: /pedido <número do produto>\nEx: /pedido 1")
        return

    try:
        produto_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("O número do produto deve ser um número inteiro.")
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nome, preco FROM produtos WHERE id = %s AND disponivel = TRUE", (produto_id,))
    produto = cur.fetchone()

    if not produto:
        await update.message.reply_text("Produto não encontrado ou indisponível.")
        cur.close()
        conn.close()
        return

    cur.execute(
        "INSERT INTO pedidos (usuario_id, produto_id, status) VALUES (%s, %s, 'pendente') RETURNING id",
        (usuario_id, produto_id)
    )
    pedido_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(
        f"Pedido #{pedido_id} realizado!\n"
        f"Produto: {produto[0]}\n"
        f"Valor: R$ {produto[1]:.2f}\n"
        f"Status: Pendente"
    )

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pe.id, pr.nome, pe.status, pe.criado_em
        FROM pedidos pe
        JOIN produtos pr ON pr.id = pe.produto_id
        WHERE pe.usuario_id = %s
        ORDER BY pe.criado_em DESC
        LIMIT 1
        """,
        (usuario_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        await update.message.reply_text("📭 Você ainda não fez nenhum pedido.")
        return

    await update.message.reply_text(
        f"*Seu último pedido:*\n\n"
        f"Pedido: #{row[0]}\n"
        f"Produto: {row[1]}\n"
        f"Status: {row[2].capitalize()}\n"
        f"Data: {row[3].strftime('%d/%m/%Y %H:%M')}",
        parse_mode="Markdown"
    )
