# ========== MAIN ==========
async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    await app.bot.set_webhook(WEBHOOK_URL + BOT_TOKEN, drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("trading", trading))
    app.add_handler(CommandHandler("voz_firma", voz_firma))
    app.add_handler(CommandHandler("estado", estado))
    app.add_handler(CommandHandler("quantum_predict", quantum_predict))
    app.add_handler(CommandHandler("sharia_check", sharia_check))
    app.add_handler(CommandHandler("quantum_portfolio", quantum_portfolio))
    app.add_handler(CommandHandler("bolsa", bolsa))
    app.add_handler(CommandHandler("finanzas_globales", finanzas_globales))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if WEBHOOK_URL is None or BOT_TOKEN is None:
        raise ValueError("❌ WEBHOOK_URL o BOT_TOKEN no están definidos.")

    webhook_url = WEBHOOK_URL + BOT_TOKEN

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8445)),
        url_path=BOT_TOKEN,
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())


