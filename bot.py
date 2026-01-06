import telebot
from telebot import types

# ================= CONFIG =================
API_TOKEN = "7890473805:AAF0NRNZkuDgfazGP6fM9_73ylWQ6FdlWtA"
ADMIN_ID = 6411738756:

bot = telebot.TeleBot(API_TOKEN)

# ================= DATABASE (memory) =================
users = {}          # user_id: {balance, state, temp}
orders = {}         # order_id: order_data
services = {}       # key: service_data
order_id_counter = 1000


# ================= KEYBOARDS =================
def main_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Buy Services", "➕ Add Funds")
    kb.add("👛 Balance", "📦 My Orders")
    kb.add("📞 Support")
    return kb


def back_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Back")
    return kb


def services_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for key, srv in services.items():
        if srv["enabled"]:
            kb.add(f"🛍 {srv['name']} ({key})")
    kb.add("⬅ Back")
    return kb


# ================= START =================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    users.setdefault(uid, {"balance": 0, "state": None, "temp": {}})

    bot.send_message(
        msg.chat.id,
        "🔥 *ENDGAME MANUAL SMM BOT*\n\n"
        "✅ Manual Orders\n"
        "✅ Admin Controlled\n"
        "❌ No Auto / No Fake\n\n"
        "Use buttons below 👇",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )


# ================= MAIN HANDLER =================
@bot.message_handler(func=lambda m: True)
def handler(msg):
    uid = msg.from_user.id
    text = msg.text
    users.setdefault(uid, {"balance": 0, "state": None, "temp": {}})

    # ---------- MAIN MENU ----------
    if text == "🛒 Buy Services":
        if not services:
            bot.send_message(msg.chat.id, "❌ No services available")
        else:
            bot.send_message(msg.chat.id, "Select a service:", reply_markup=services_kb())

    elif text.startswith("🛍"):
        key = text.split("(")[-1].replace(")", "")
        if key in services and services[key]["enabled"]:
            users[uid]["state"] = "LINK"
            users[uid]["temp"]["service"] = key
            bot.send_message(msg.chat.id, "🔗 Send Telegram post link", reply_markup=back_kb())

    elif text == "👛 Balance":
        bot.send_message(msg.chat.id, f"👛 Balance: ₹{users[uid]['balance']:.2f}")

    elif text == "📦 My Orders":
        show_my_orders(msg)

    elif text == "➕ Add Funds":
        bot.send_message(
            msg.chat.id,
            "💳 Pay & send SS to admin\n\nUPI: mohammadasif01@fam"
        )

    elif text == "📞 Support":
        bot.send_message(msg.chat.id, "Admin: @SPEEDxOP_01")

    elif text == "⬅ Back":
        users[uid]["state"] = None
        users[uid]["temp"] = {}
        bot.send_message(msg.chat.id, "Main Menu", reply_markup=main_kb())

    # ---------- STATES ----------
    elif users[uid]["state"] == "LINK":
        if "t.me/" not in text:
            bot.send_message(msg.chat.id, "❌ Invalid Telegram link")
            return
        users[uid]["temp"]["link"] = text
        users[uid]["state"] = "QTY"
        srv = services[users[uid]["temp"]["service"]]
        bot.send_message(
            msg.chat.id,
            f"📦 Enter quantity (min {srv['min']})"
        )

    elif users[uid]["state"] == "QTY":
        if not text.isdigit():
            bot.send_message(msg.chat.id, "❌ Enter valid number")
            return

        qty = int(text)
        srv = services[users[uid]["temp"]["service"]]

        if qty < srv["min"]:
            bot.send_message(msg.chat.id, f"❌ Minimum {srv['min']}")
            return

        create_order(msg, qty)


# ================= CREATE ORDER =================
def create_order(msg, qty):
    global order_id_counter
    uid = msg.from_user.id
    srv_key = users[uid]["temp"]["service"]
    srv = services[srv_key]

    cost = (qty / 100) * srv["price"]
    order_id_counter += 1

    orders[order_id_counter] = {
        "user": uid,
        "service": srv["name"],
        "qty": qty,
        "cost": cost,
        "link": users[uid]["temp"]["link"],
        "status": "PENDING"
    }

    bot.send_message(
        msg.chat.id,
        f"✅ *ORDER PLACED*\n\n"
        f"🆔 Order ID: `{order_id_counter}`\n"
        f"📊 Service: {srv['name']}\n"
        f"📦 Qty: {qty}\n"
        f"💰 Cost: ₹{cost:.2f}\n"
        f"⏳ Status: PENDING\n\n"
        f"Admin will process manually.",
        parse_mode="Markdown",
        reply_markup=main_kb()
    )

    bot.send_message(
        ADMIN_ID,
        f"🆕 *NEW MANUAL ORDER*\n\n"
        f"Order ID: `{order_id_counter}`\n"
        f"User: `{uid}`\n"
        f"Service: {srv['name']}\n"
        f"Qty: {qty}\n"
        f"Cost: ₹{cost:.2f}\n\n"
        f"/complete {order_id_counter}\n"
        f"/reject {order_id_counter} reason",
        parse_mode="Markdown"
    )

    users[uid]["state"] = None
    users[uid]["temp"] = {}


# ================= MY ORDERS =================
def show_my_orders(msg):
    uid = msg.from_user.id
    text = "📦 *Your Orders*\n\n"
    found = False

    for oid, o in orders.items():
        if o["user"] == uid:
            found = True
            emoji = "⏳" if o["status"] == "PENDING" else "✅" if o["status"] == "COMPLETED" else "❌"
            text += (
                f"🆔 #{oid}\n"
                f"Service: {o['service']}\n"
                f"Qty: {o['qty']}\n"
                f"Amount: ₹{o['cost']:.2f}\n"
                f"Status: {emoji} {o['status']}\n\n"
            )

    if not found:
        text = "📦 No orders yet."

    bot.send_message(msg.chat.id, text, parse_mode="Markdown")


# ================= ADMIN COMMANDS =================
@bot.message_handler(commands=["addbalance"])
def add_balance(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    _, uid, amt = msg.text.split()
    uid = int(uid)
    amt = float(amt)
    users.setdefault(uid, {"balance": 0, "state": None, "temp": {}})
    users[uid]["balance"] += amt
    bot.send_message(uid, f"✅ Balance added: ₹{amt}")
    bot.send_message(ADMIN_ID, "✅ Balance updated")


@bot.message_handler(commands=["complete"])
def complete_order(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    _, oid = msg.text.split()
    oid = int(oid)

    if oid not in orders:
        bot.send_message(ADMIN_ID, "❌ Invalid Order ID")
        return

    order = orders[oid]
    uid = order["user"]

    if users[uid]["balance"] < order["cost"]:
        bot.send_message(ADMIN_ID, "❌ User has insufficient balance")
        return

    users[uid]["balance"] -= order["cost"]
    order["status"] = "COMPLETED"

    bot.send_message(
        uid,
        f"✅ *ORDER COMPLETED*\n\n"
        f"Order ID: `{oid}`\n"
        f"Remaining Balance: ₹{users[uid]['balance']:.2f}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["reject"])
def reject_order(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split(maxsplit=2)
    oid = int(parts[1])
    reason = parts[2] if len(parts) > 2 else "No reason"

    if oid not in orders:
        bot.send_message(ADMIN_ID, "❌ Invalid Order ID")
        return

    orders[oid]["status"] = "REJECTED"
    bot.send_message(
        orders[oid]["user"],
        f"❌ *ORDER REJECTED*\n\nOrder ID: `{oid}`\nReason: {reason}",
        parse_mode="Markdown"
    )


# ================= SERVICE MANAGER =================
@bot.message_handler(commands=["addservice"])
def add_service(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    try:
        _, key, name, price, minq = msg.text.split(maxsplit=4)
        services[key] = {
            "name": name,
            "price": float(price),
            "min": int(minq),
            "enabled": True
        }
        bot.send_message(ADMIN_ID, f"✅ Service added: {name}")
    except:
        bot.send_message(ADMIN_ID, "❌ Format: /addservice key name price min")


@bot.message_handler(commands=["services"])
def list_services(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    if not services:
        bot.send_message(ADMIN_ID, "No services")
        return

    text = "📋 *Services*\n\n"
    for k, s in services.items():
        text += f"{k} | {s['name']} | ₹{s['price']} | Min {s['min']} | {'ON' if s['enabled'] else 'OFF'}\n"
    bot.send_message(ADMIN_ID, text, parse_mode="Markdown")


@bot.message_handler(commands=["toggleservice"])
def toggle_service(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    _, key = msg.text.split()
    if key in services:
        services[key]["enabled"] = not services[key]["enabled"]
        bot.send_message(ADMIN_ID, f"✅ Service {key} toggled")


# ================= RUN =================
print("🔥 ENDGAME MANUAL SMM BOT RUNNING")
bot.polling(none_stop=True)