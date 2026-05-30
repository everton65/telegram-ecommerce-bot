from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from db.connection import get_db
from urllib.parse import quote

# teclado permanente

MENU_INLINE = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🛍️ Produtos", callback_data="produtos"),
        InlineKeyboardButton("📦 Pedidos", callback_data="status")
    ],
    [
        InlineKeyboardButton("🔥 Promoções", callback_data="promocoes"),
        InlineKeyboardButton("ℹ️ Ajuda", callback_data="ajuda")
    ]
])

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
            InlineKeyboardButton("📦 Meus Pedidos", callback_data="status")
        ],
        [
            InlineKeyboardButton("🔥 Promoções", callback_data="promocoes"),
            InlineKeyboardButton("ℹ️ Ajuda", callback_data="ajuda")
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
            f"   ▶️ /produto {row[0]}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MENU_INLINE)

# /pedido
async def pedido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "⚠️ *Como fazer um pedido:*\n\n"
            "Digite `/produto` seguido do ID do produto\n\n"
            "📌 Exemplo: `/produto 1`\n\n"
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
    nome_produto = produto[0]

    mensagem_wpp = "Olá! Quero finalizar meu pedido:%0A%0A🛒 " + nome_produto + "%0A💰 " + preco + "%0A🆔 Pedido #" + str(pedido_id)
    link_wpp = "https://wa.me/5581979018628?text=" + mensagem_wpp.replace(" ", "%20")

    botao_finalizar = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Finalizar Compra no WhatsApp", url=link_wpp)],
        [
            InlineKeyboardButton("🛍️ Produtos", callback_data="produtos"),
            InlineKeyboardButton("📦 Pedidos", callback_data="status")
        ]
    ])

    await update.message.reply_text(
        f"✅ *{nome_produto} adicionado com sucesso!*\n\n"
        f"🛒 *{nome_produto}*\n"
        f"💰 {preco}\n"
        f"📌 Status: ⏳ Pendente\n"
        f"🆔 Pedido #{pedido_id}\n\n"
        f"_Clique abaixo para finalizar sua compra:_",
        parse_mode="Markdown",
        reply_markup=botao_finalizar
    )
    

# /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.effective_user.id

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT ON (pr.nome) pe.id, pr.nome, pr.preco, pe.status, pe.criado_em, COUNT(*) OVER (PARTITION BY pr.nome) as quantidade
                    FROM pedidos pe
                    JOIN produtos pr ON pr.id = pe.produto_id
                    WHERE pe.usuario_id = %s
                    ORDER BY pr.nome, pe.criado_em DESC
                    """,
                    (usuario_id,)
                )
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao buscar pedidos. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text(
            "📭 *Você ainda não possui pedidos.*\n\n"
            "🛍️ Clique em *Produtos* para ver o catálogo.",
            parse_mode="Markdown",
            reply_markup=MENU_INLINE
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
    resumo_wpp = "Olá! Quero finalizar meus pedidos:%0A%0A"

    for row in rows:
        preco = f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        status_texto = status_emoji.get(row[3], row[3].capitalize())
        quantidade = row[5]
        qtd_txt = f" (x{quantidade})" if quantidade > 1 else ""
        msg += (
            f"━━━━━━━━━━━━━━━\n"
            f"🆔 Pedido #{row[0]}\n"
            f"🛒 *{row[1]}*{qtd_txt}\n"
            f"💰 {preco}\n"
            f"📌 {status_texto}\n"
            f"📅 {row[4].strftime('%d/%m/%Y')} às {row[4].strftime('%H:%M')}\n\n"
        )
        linha = f"- {row[1]}{qtd_txt} - {preco}\n- Pedido #{row[0]}\n\n"
        resumo_wpp += quote(linha)

    link_wpp = "https://wa.me/5581979018628?text=" + resumo_wpp.replace(" ", "%20")

    botao_finalizar = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Finalizar Compra no WhatsApp", url=link_wpp)],
        [
            InlineKeyboardButton("🛍️ Produtos", callback_data="produtos"),
            InlineKeyboardButton("🔥 Promoções", callback_data="promocoes")
        ],
        [
            InlineKeyboardButton("📦 Pedidos", callback_data="status"),
            InlineKeyboardButton("ℹ️ Ajuda", callback_data="ajuda")
        ]
    ])

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=botao_finalizar)

# /promocoes
async def promocoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT produto, preco, loja, link
                    FROM promocoes
                    ORDER BY criado_em DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao buscar promoções. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text(
            "⚠️ Nenhuma promoção disponível.",
            reply_markup=MENU_INLINE
        )
        return

    numeros = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    msg = "🔥 *TOP PROMOÇÕES*\n\n"

    for i, row in enumerate(rows):
        numero = numeros[i] if i < len(numeros) else f"{i+1}."
        preco = f"R$ {row[1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        link_texto = f"\n   🔗 [Ver oferta]({row[3]})" if row[3] else ""
        msg += (
            f"{numero} *{row[0]}*\n"
            f"   💰 {preco}\n"
            f"   🏪 {row[2]}{link_texto}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=MENU_INLINE)

# /buscar
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🔎 *Como buscar um produto:*\n\n"
            "Digite `/buscar` seguido do nome\n\n"
            "📌 Exemplo: `/buscar cadeira`",
            parse_mode="Markdown"
        )
        return

    termo = " ".join(context.args)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, nome, descricao, preco
                    FROM produtos
                    WHERE disponivel = TRUE
                    AND (nome ILIKE %s OR descricao ILIKE %s)
                """, (f"%{termo}%", f"%{termo}%"))
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao buscar. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text(
            f"😕 Nenhum produto encontrado para *{termo}*.\n\n"
            "Use /produtos para ver o catálogo completo.",
            parse_mode="Markdown"
        )
        return

    msg = f"🔎 *Resultados para \"{termo}\"*\n\n"
    for row in rows:
        preco = f"R$ {row[3]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        msg += (
            f"📦 *{row[1]}*\n"
            f"   📝 {row[2]}\n"
            f"   💰 {preco}\n"
            f"   🛒 /produto {row[0]}\n\n"
        )

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MENU_INLINE)

# /admin
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM usuarios")
                total_usuarios = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM pedidos")
                total_pedidos = cur.fetchone()[0]

                cur.execute("""
                    SELECT COALESCE(SUM(pr.preco), 0)
                    FROM pedidos pe
                    JOIN produtos pr ON pr.id = pe.produto_id
                """)
                faturamento = cur.fetchone()[0]

                cur.execute("""
                    SELECT pr.nome, COUNT(*) as total
                    FROM pedidos pe
                    JOIN produtos pr ON pr.id = pe.produto_id
                    GROUP BY pr.nome
                    ORDER BY total DESC
                    LIMIT 1
                """)
                mais_vendido = cur.fetchone()
    except Exception:
        await update.message.reply_text("❌ Erro ao carregar painel. Tente novamente.")
        return

    faturamento_fmt = f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    mais_vendido_txt = f"{mais_vendido[0]} ({mais_vendido[1]} pedidos)" if mais_vendido else "Nenhum ainda"

    await update.message.reply_text(
        "📊 *PAINEL ADMINISTRATIVO*\n\n"
        "━━━━━━━━━━━━━━━\n"
        f"👥 Usuários cadastrados: *{total_usuarios}*\n"
        f"📦 Total de pedidos: *{total_pedidos}*\n"
        f"💰 Faturamento total: *{faturamento_fmt}*\n"
        f"🏆 Produto mais vendido: *{mais_vendido_txt}*\n"
        "━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
        reply_markup=MENU_INLINE
    )

# /ranking
async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT pr.nome, COUNT(*) as total
                    FROM pedidos pe
                    JOIN produtos pr ON pr.id = pe.produto_id
                    GROUP BY pr.nome
                    ORDER BY total DESC
                    LIMIT 10
                """)
                rows = cur.fetchall()
    except Exception:
        await update.message.reply_text("❌ Erro ao carregar ranking. Tente novamente.")
        return

    if not rows:
        await update.message.reply_text("📭 Ainda não há pedidos para gerar o ranking.")
        return

    medalhas = ["🥇", "🥈", "🥉"]
    numeros = ["4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    msg = "🏆 *PRODUTOS MAIS VENDIDOS*\n\n"

    for i, row in enumerate(rows):
        icone = medalhas[i] if i < 3 else numeros[i - 3]
        msg += f"{icone} *{row[0]}* — {row[1]} pedido(s)\n"

    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=MENU_INLINE)

# /ajuda
async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *AJUDA — COMANDOS DISPONÍVEIS*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🏠 /start — Iniciar o bot\n"
        "🛍️ /produtos — Ver catálogo completo\n"
        "🛒 /produto <id> — Adicionar ao carrinho\n"
        "📦 /status — Ver seus pedidos\n"
        "🔎 /buscar <nome> — Buscar produto\n"
        "🔥 /promocoes — Ver promoções\n"
        "🏆 /ranking — Produtos mais vendidos\n"
        "📊 /admin — Painel administrativo\n"
        "━━━━━━━━━━━━━━━\n\n"
        "💡 *Exemplos:*\n"
        "`/produto 1`\n"
        "`/buscar camiseta`",
        parse_mode="Markdown",
        reply_markup=MENU_INLINE
    )

# menu permanente — trata textos dos botões
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    if texto == "🏠 Menu Principal":
        await start(update, context)
    elif texto == "🛍️ Produtos":
        await produtos(update, context)
    elif texto == "📦 Meus Pedidos":
        await status(update, context)
    elif texto == "🔥 Promoções":
        await promocoes(update, context)
    elif texto == "ℹ️ Ajuda":
        await ajuda(update, context)

# callback dos botões inline do /start
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "produtos":
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, nome, descricao, preco FROM produtos WHERE disponivel = TRUE")
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
                f"   🛒 /produto {row[0]}\n\n"
            )
        await query.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=MENU_INLINE
        )

    elif query.data == "status":
        usuario_id = query.from_user.id
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT ON (pr.nome) pe.id, pr.nome, pr.preco, pe.status, pe.criado_em, COUNT(*) OVER (PARTITION BY pr.nome) as quantidade
                        FROM pedidos pe
                        JOIN produtos pr ON pr.id = pe.produto_id
                        WHERE pe.usuario_id = %s
                        ORDER BY pr.nome, pe.criado_em DESC
                        """,
                        (usuario_id,)
                    )
                    rows = cur.fetchall()
        except Exception:
            await query.message.reply_text("❌ Erro ao buscar pedidos.")
            return

        if not rows:
            await query.message.reply_text(
                "📭 *Você ainda não possui pedidos.*\n\nUse /produtos para ver o catálogo.",
                parse_mode="Markdown",
                reply_markup=MENU_INLINE
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
        resumo_wpp = "Olá! Quero finalizar meus pedidos:%0A%0A"

        for row in rows:
            preco = f"R$ {row[2]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            status_texto = status_emoji.get(row[3], row[3].capitalize())
            quantidade = row[5]
            qtd_txt = f" (x{quantidade})" if quantidade > 1 else ""
            msg += (
                f"━━━━━━━━━━━━━━━\n"
                f"🆔 Pedido #{row[0]}\n"
                f"🛒 *{row[1]}*{qtd_txt}\n"
                f"💰 {preco}\n"
                f"📌 {status_texto}\n"
                f"📅 {row[4].strftime('%d/%m/%Y')} às {row[4].strftime('%H:%M')}\n\n"
            )
            linha = f"- {row[1]}{qtd_txt} - {preco}\n- Pedido #{row[0]}\n\n"
            resumo_wpp += quote(linha)

        link_wpp = "https://wa.me/5581979018628?text=" + quote("Ola! Quero finalizar meus pedidos:\n\n") + resumo_wpp.replace("+", "%20")

        botao_finalizar = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Finalizar Compra no WhatsApp", url=link_wpp)],
            [
                InlineKeyboardButton("🛍️ Produtos", callback_data="produtos"),
                InlineKeyboardButton("🔥 Promoções", callback_data="promocoes")
            ],
            [
                InlineKeyboardButton("📦 Pedidos", callback_data="status"),
                InlineKeyboardButton("ℹ️ Ajuda", callback_data="ajuda")
            ]
        ])

        await query.message.reply_text(msg, parse_mode="Markdown", reply_markup=botao_finalizar)

    elif query.data == "promocoes":
        try:
            with get_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT produto, preco, loja, link FROM promocoes ORDER BY criado_em DESC LIMIT 10")
                    rows = cur.fetchall()
        except Exception:
            await query.message.reply_text("❌ Erro ao buscar promoções.")
            return

        if not rows:
            await query.message.reply_text("⚠️ Nenhuma promoção disponível.")
            return

        numeros = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
        msg = "🔥 *TOP PROMOÇÕES*\n\n"
        for i, row in enumerate(rows):
            numero = numeros[i] if i < len(numeros) else f"{i+1}."
            preco = f"R$ {row[1]:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            link_texto = f"\n   🔗 [Ver oferta]({row[3]})" if row[3] else ""
            msg += f"{numero} *{row[0]}*\n   💰 {preco}\n   🏪 {row[2]}{link_texto}\n\n"
        await query.message.reply_text(
            msg,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=MENU_INLINE
        )

    elif query.data == "ajuda":
        await query.message.reply_text(
            "ℹ️ *AJUDA — COMANDOS DISPONÍVEIS*\n\n"
            "━━━━━━━━━━━━━━━\n"
            "🏠 /start — Iniciar o bot\n"
            "🛍️ /produtos — Ver catálogo completo\n"
            "🛒 /produto <id> — Adicionar ao carrinho\n"
            "📦 /status — Ver seus pedidos\n"
            "🔎 /buscar <nome> — Buscar produto\n"
            "🔥 /promocoes — Ver promoções\n"
            "🏆 /ranking — Produtos mais vendidos\n"
            "📊 /admin — Painel administrativo\n"
            "━━━━━━━━━━━━━━━\n\n"
            "💡 *Exemplos:*\n"
            "`/produto 1`\n"
            "`/buscar camiseta`",
            parse_mode="Markdown",
            reply_markup=MENU_INLINE
        )