import asyncio
import time

def news_loop():
    while True:
        news = get_real_news()

        if news:
            users = get_users()

            async def run():
                for u in users:
                    for n in news:
                        try:
                            await bot_app.bot.send_message(chat_id=u, text=n)
                        except:
                            pass

            asyncio.run(run())

        time.sleep(120)
