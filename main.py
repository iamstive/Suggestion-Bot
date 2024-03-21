import telebot


bot = telebot.TeleBot("6745051528:AAGi7tI2a0eAsTdSPGQeOIu3rWSue1drGIM")


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Добро пожаловать')


bot.polling(none_stop=True)
