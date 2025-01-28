from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random

user_balances = {}


START_BALANCE = 1000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE
    await update.message.reply_text(
        f"🎰 Добро пожаловать в Казино!\n"
        f"💰 Ваш начальный баланс: {user_balances[user_id]}$\n"
        "Доступные команды:\n"
        "/balance - Проверить баланс\n"
        "/casino - Играть в рулетку или блэкджек\n"
        "/russian_roulette - Играть в русскую рулетку"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)
    await update.message.reply_text(f"💰 Ваш текущий баланс: {balance}$")



async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎲 Рулетка", callback_data="roulette")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="blackjack")]
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
        loss = 100
        user_balances[user_id] -= loss
        await query.message.reply_text(
            f"😢 Выпало {bet}, вы поставили {user_bet}. -{loss}$\n💰 Баланс: {user_balances[user_id]}$")



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
        await update.message.reply_text(
            f"😅 Щелк! Вам повезло, барабан пуст! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")



def main():
    TOKEN = "7771538325:AAFS1STLG3C47o7-Nk6_htSV9e51A9A_1q0"
    app = ApplicationBuilder().token(TOKEN).build()


    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("casino", casino))
    app.add_handler(CommandHandler("russian_roulette", russian_roulette))


    app.add_handler(CallbackQueryHandler(roulette, pattern="^roulette$"))
    app.add_handler(CallbackQueryHandler(blackjack, pattern="^blackjack$"))


    app.run_polling()


if __name__ == "__main__":
    main()