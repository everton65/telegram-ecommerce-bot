from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.connection import get_db

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario = update.effective_user

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO usuarios (id, nome) VALUES (%s, %s) ON CONFLICT (id) DO NOTHING",
                    (usuario.id, usuario.first_name)
                )
    except Exception:
        await update.message.reply_text("❌ Erro ao registrar usuário. Tente novamente.")
        return

    keyboard = [
        [
            InlineKeyboardButton("🛍️ Ver Produtos", callback_data="produtos"),
            InlineKeyboardButton("📋 Meu Pedido", callback_data="status")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Olá, *{usuario.first_name or 'Cliente'}*!\n\n"
        "🛒 *Bem-vindo à Loja Santos Bot*\n\n"
        "O que você deseja fazer hoje?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# /produtos
async def produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, nome, descricao, preco
                    FROM produtos
                    WHERE disponivel = TRUE
                """)
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao buscar produtos. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text("⚠️ Nenhum produto disponível no momento.")
        return

    numeros = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

    msg = "🛍️ *CATÁLOGO DE PRODUTOS*\n\n"

    for i, row in enumerate(rows):
        numero = numeros[i] if i < len(numeros) else f"{i+1}."
        preco = f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        msg += (
            f"{numero} *{row[1]}*\n"
            f"   📝 {row[2]}\n"
            f"   💰 {preco}\n"
            f"   ▶️ /pedido {row[0]}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown")

# /pedido
async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "⚠️ *Como fazer um pedido:*\n\n"
            "Digite `/pedido` seguido do ID do produto\n\n"
            "📌 Exemplo: `/pedido 1`\n\n"
            "Use /produtos para ver os IDs disponíveis.",
            parse_mode="Markdown"
        )
        return

    try:
        produto_id = int(context.args[0])
        if produto_id <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ O ID do produto deve ser um número válido.")
        return

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT nome, preco FROM produtos WHERE id = %s AND disponivel = TRUE",
                    (produto_id,)
                )
                produto = cur.fetchone()

                if not produto:
                    await update.message.reply_text(
                        "❌ Produto não encontrado ou indisponível.\n\n"
                        "Use /produtos para ver os itens disponíveis."
                    )
                    return

                cur.execute(
                    "INSERT INTO pedidos (usuario_id, produto_id, status) VALUES (%s, %s, 'pendente') RETURNING id",
                    (usuario_id, produto_id)
                )
                pedido_id = cur.fetchone()[0]
    except Exception:
        await update.message.reply_text("❌ Erro ao realizar pedido. Tente novamente.")
        return

    preco = f"R$ {produto[1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    await update.message.reply_text(
        f"✅ *Pedido realizado com sucesso!*\n\n"
        f"🛒 *{produto[0]}*\n"
        f"💰 {preco}\n"
        f"📌 Status: ⏳ Pendente\n"
        f"🆔 Pedido #{pedido_id}\n\n"
        f"_Acompanhe pelo /status_",
        parse_mode="Markdown"
    )

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT pe.id, pr.nome, pr.preco, pe.status, pe.criado_em
                    FROM pedidos pe
                    JOIN produtos pr ON pr.id = pe.produto_id
                    WHERE pe.usuario_id = %s
                    ORDER BY pe.criado_em DESC
                    """,
                    (usuario_id,)
                )
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao buscar pedido. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text(
            "📭 *Você ainda não possui pedidos.*\n\n"
            "Use /produtos para ver o catálogo.",
            parse_mode="Markdown"
        )
        return

    status_emoji = {
        "pendente": "⏳ Pendente",
        "confirmado": "✅ Confirmado",
        "enviado": "🚚 Enviado",
        "entregue": "📦 Entregue",
        "cancelado": "❌ Cancelado"
    }

    msg = "📋 *SEUS PEDIDOS*\n\n"

    for row in rows:
        preco = f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        status_texto = status_emoji.get(row[3], row[3].capitalize())

        msg += (
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 Pedido #{row[0]}\n"
            f"🛒 *{row[1]}*\n"
            f"💰 {preco}\n"
            f"📌 {status_texto}\n"
            f"📅 {row[4].strftime('%d/%m/%Y')} às {row[4].strftime('%H:%M')}\n\n"
        )

    await update.message.reply_text(
        msg,
        parse_mode="Markdown"
    )

# callback dos botões do /start
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "produtos":
        # chama diretamente o banco
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, nome, descricao, preco
                        FROM produtos
                        WHERE disponivel = TRUE
                    """)
                    rows = cur.fetchall()
        except Exception:
            await query.message.reply_text("❌ Erro ao buscar produtos.")
            return

        numeros = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        msg = "🛍️ *CATÁLOGO DE PRODUTOS*\n\n"
        for i, row in enumerate(rows):
            numero = numeros[i] if i < len(numeros) else f"{i+1}."
            preco = f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            msg += (
                f"{numero} *{row[1]}*\n"
                f"   📝 {row[2]}\n"
                f"   💰 {preco}\n"
                f"   ▶️ /pedido {row[0]}\n\n"
            )
        await query.message.reply_text(msg, parse_mode="Markdown")

    elif query.data == "status":
        usuario_id = query.from_user.id
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT pe.id, pr.nome, pr.preco, pe.status, pe.criado_em
                        FROM pedidos pe
                        JOIN produtos pr ON pr.id = pe.produto_id
                        WHERE pe.usuario_id = %s
                        ORDER BY pe.criado_em DESC
                        """,
                        (usuario_id,)
                    )
                    rows = cur.fetchall()
        except Exception:
            await query.message.reply_text("❌ Erro ao buscar pedido.")
            return

        if not rows:
            await query.message.reply_text(
                "📭 *Você ainda não possui pedidos.*\n\nUse /produtos para ver o catálogo.",
                parse_mode="Markdown"
            )
            return

        status_emoji = {
            "pendente": "⏳ Pendente",
            "confirmado": "✅ Confirmado",
            "enviado": "🚚 Enviado",
            "entregue": "📦 Entregue",
            "cancelado": "❌ Cancelado"
        }

        msg = "📋 *SEUS PEDIDOS*\n\n"

        for row in rows:
            preco = f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            status_texto = status_emoji.get(row[3], row[3].capitalize())

            msg += (
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 Pedido #{row[0]}\n"
                f"🛒 *{row[1]}*\n"
                f"💰 {preco}\n"
                f"📌 {status_texto}\n"
                f"📅 {row[4].strftime('%d/%m/%Y')} às {row[4].strftime('%H:%M')}\n\n"
            )

        await query.message.reply_text(
            msg,
            parse_mode="Markdown"
        )