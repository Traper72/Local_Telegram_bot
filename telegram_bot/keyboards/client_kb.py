from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

b1 = KeyboardButton('/Помощь')
b2 = KeyboardButton('/Связаться_с_оператором')
b3 = KeyboardButton('/Письмо_в_техподдержку')

kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client.add(b1).row(b2, b3)
