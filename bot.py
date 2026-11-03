import asyncio
import os
import sqlite3
from aiohttp import web
from vkbottle.bot import Bot

VK_TOKEN = "vk1.a.PR8o3N6O5btbGNIh4PzEZNulqJv3YDkkdhzH-XRhhlpzkFcs8tPt0qbbXurRrbi70TUnBiO8Jb3mjeXHPRUw2NpkdkExLdQ--SUcT1Y8BzBPf_5OdPk3-M4wnwU9gjcSlnVVXbyjZyXqmMkG97TzMmN4vFBb0DIqOfa8o6f76k5fooN1FzfUQtVtggnn7Iz4OuwSTi90vcONXngH3oicuQ"
VK_CONFIRMATION = "c3716efe"
VK_SECRET = "seCreTT2341botse"

GOODS = {
    "15811150": "https://disk.yandex.ru/i/9yg8Bt__QUq25g",
    "15811157": "https://disk.yandex.ru/i/45m5k9QPUaS49Q",
    "15818279": "https://disk.yandex.ru/i/83TAui6xAdZqHQ",
}

bot = Bot(token=VK_TOKEN)
DB_PATH = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS processed_orders (order_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_processed(order_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM processed_orders WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def mark_processed(order_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO processed_orders (order_id) VALUES (?)", (order_id,))
    conn.commit()
    conn.close()

@bot.on.raw_event("market_order_new")
@bot.on.raw_event("market_order_edit")
async def handle_order(event: dict):
    obj = event.get("object", {})
    order_id = obj.get("id")
    if not order_id or is_processed(order_id):
        return

    payment_status = obj.get("payment_status")
    status = obj.get("status")
    if payment_status != "paid" and status != 4:
        return

    user_id = obj.get("user_id")
    if not user_id:
        return

    items = obj.get("preview_order_items", [])
    for item in items:
        item_id = str(item.get("id"))
        if item_id in GOODS:
            await bot.api.messages.send(
                user_id=user_id,
                message=f"✅ Спасибо за покупку! Ваш товар:\n{GOODS[item_id]}",
                random_id=0
            )
    mark_processed(order_id)

async def vk_callback(request: web.Request):
    body = await request.json()
    if body.get("secret") != VK_SECRET:
        return web.Response(status=403, text="Forbidden")
    if body.get("type") == "confirmation":
        return web.Response(text=VK_CONFIRMATION)
    emulation = await bot.emulate(body)
    return web.Response(text=emulation or "ok")

async def main():
    init_db()
    app = web.Application()
    app.router.add_post("/vk/callback", vk_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Сервер запущен на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())