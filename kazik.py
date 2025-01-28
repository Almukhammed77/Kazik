from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import random

user_balances = {}

START_BALANCE = 1000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE
    await update.message.reply_text(
        f"🎰 Добро пожаловать в Казино!\n"
        f"💰 Ваш баланс: {user_balances[user_id]}$\n"
        "Доступные команды:\n"
        "/balance - Проверить баланс\n"
        "/casino - Играть в рулетку, блэкджек, кости и покер\n"
        "/russian_roulette - Играть в русскую рулетку"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)
    await update.message.reply_text(f"💰 Ваш текущий баланс: {balance}$")


async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎲 Рулетка", callback_data="roulette")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="blackjack")],
        [InlineKeyboardButton("🎲 Кости", callback_data="dice")],
        [InlineKeyboardButton("🃏 Покер", callback_data="poker")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите игру:", reply_markup=reply_markup)


async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if balance < 100:
        await query.message.reply_text("❌ У вас недостаточно денег для игры в рулетку!")
        return

    bet = random.randint(0, 36)
    user_bet = random.randint(0, 36)

    if bet == user_bet:
        winnings = 500
        user_balances[user_id] += winnings
        await query.message.reply_text(f"🎉 Выпало {bet}, вы угадали! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        user_balances[user_id] -= 100
        await query.message.reply_text(f"😢 Выпало {bet}, вы поставили {user_bet}. -100$\n💰 Баланс: {user_balances[user_id]}$")


async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if balance < 100:
        await query.message.reply_text("❌ У вас недостаточно денег для игры в блэкджек!")
        return

    user_cards = [random.randint(1, 11) for _ in range(2)]
    dealer_cards = [random.randint(1, 11) for _ in range(2)]
    user_total = sum(user_cards)
    dealer_total = sum(dealer_cards)

    await query.message.reply_text(
        f"🃏 Ваши карты: {user_cards} (сумма: {user_total})\n"
        f"🃏 Карты дилера: {dealer_cards} (сумма: {dealer_total})"
    )

    if user_total > 21:
        user_balances[user_id] -= 100
        await query.message.reply_text(f"😢 Перебор! -100$\n💰 Баланс: {user_balances[user_id]}$")
    elif dealer_total > 21 or user_total > dealer_total:
        user_balances[user_id] += 200
        await query.message.reply_text(f"🎉 Вы выиграли! +200$\n💰 Баланс: {user_balances[user_id]}$")
    elif user_total == dealer_total:
        await query.message.reply_text(f"🤝 Ничья! Баланс не изменился.\n💰 Баланс: {user_balances[user_id]}$")
    else:
        user_balances[user_id] -= 100
        await query.message.reply_text(f"😢 Вы проиграли! -100$\n💰 Баланс: {user_balances[user_id]}$")


async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if balance < 50:
        await query.message.reply_text("❌ У вас недостаточно денег для игры в кости!")
        return

    player_throw = random.randint(1, 6)
    bot_throw = random.randint(1, 6)

    await query.message.reply_text(f"🎲 Вы выбросили {player_throw}, бот выбросил {bot_throw}")

    if player_throw > bot_throw:
        user_balances[user_id] += 100
        await query.message.reply_text(f"🎉 Вы победили! +100$\n💰 Баланс: {user_balances[user_id]}$")
    elif player_throw < bot_throw:
        user_balances[user_id] -= 50
        await query.message.reply_text(f"😢 Вы проиграли! -50$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        await query.message.reply_text(f"🤝 Ничья! Баланс не изменился.\n💰 Баланс: {user_balances[user_id]}$")


async def poker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if balance < 200:
        await query.message.reply_text("❌ У вас недостаточно денег для игры в покер!")
        return

    hands = ["Пара", "Две пары", "Тройка", "Флеш", "Стрит", "Фулл-хаус", "Каре", "Стрит-флеш", "Роял-флеш"]
    player_hand = random.choice(hands)
    bot_hand = random.choice(hands)

    await query.message.reply_text(f"🃏 Ваша комбинация: {player_hand}\n🤖 Комбинация бота: {bot_hand}")

    if hands.index(player_hand) > hands.index(bot_hand):
        user_balances[user_id] += 500
        await query.message.reply_text(f"🎉 Вы выиграли! +500$\n💰 Баланс: {user_balances[user_id]}$")
    elif hands.index(player_hand) < hands.index(bot_hand):
        user_balances[user_id] -= 200
        await query.message.reply_text(f"😢 Вы проиграли! -200$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        await query.message.reply_text(f"🤝 Ничья! Баланс не изменился.\n💰 Баланс: {user_balances[user_id]}$")


async def russian_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if balance < 200:
        await update.message.reply_text("❌ У вас недостаточно денег для русской рулетки!")
        return

    bullet_position = random.randint(1, 6)
    trigger_pull = random.randint(1, 6)

    await update.message.reply_text("🔫 Вы подносите револьвер к виску и нажимаете на курок...")

    if bullet_position == trigger_pull:
        user_balances[user_id] = 0
        await update.message.reply_text("💥 Бах! Вы проиграли всё... 😵\n💰 Баланс: 0$")
    else:
        winnings = 300
        user_balances[user_id] += winnings
        await update.message.reply_text(f"😅 Щелк! Вам повезло, барабан пуст! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")



async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)


    if not context.args:
        await update.message.reply_text("💰 Используйте команду так: `/deposit 500` (сумма пополнения)")
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Сумма пополнения должна быть больше 0!")
            return

        user_balances[user_id] += amount
        await update.message.reply_text(
            f"✅ Вы пополнили баланс на {amount}$\n💰 Новый баланс: {user_balances[user_id]}$")

    except ValueError:
        await update.message.reply_text("❌ Введите корректное число для пополнения! Пример: `/deposit 500`")


def main():
    TOKEN = "7771538325:AAFS1STLG3C47o7-Nk6_htSV9e51A9A_1q0"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("casino", casino))
    app.add_handler(CommandHandler("russian_roulette", russian_roulette))
    app.add_handler(CommandHandler("deposit", deposit))

    app.add_handler(CallbackQueryHandler(roulette, pattern="^roulette$"))
    app.add_handler(CallbackQueryHandler(blackjack, pattern="^blackjack$"))
    app.add_handler(CallbackQueryHandler(dice, pattern="^dice$"))
    app.add_handler(CallbackQueryHandler(poker, pattern="^poker$"))

    app.run_polling()

if __name__ == "__main__":
    main()