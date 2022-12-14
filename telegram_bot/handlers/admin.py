from cmd import IDENTCHARS
from turtle import width
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import Dispatcher, types
from create_bot import dp, bot
from aiogram.dispatcher.filters import Text, Command
from database import sqlite_db
from keyboards import admin_kb
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

id_admin = None

class FSMAdmin(StatesGroup):
    photo = State()
    name = State()
    description = State()
    price = State()

#Получаем id текущего модератора
# @dp.message_handler(commands=['moderator'], is_chat_admin=True)
async def make_change_command(message: types.Message):
    global id_admin
    id_admin = message.from_user.id
    await bot.send_message(message.from_user.id, '?', reply_markup=admin_kb.btn_case_admin)
    await message.delete()

#Начало диалога загрузки нового пункта меню
# @dp.message_handler(commands='Загрузить', state=None)
async def cm_start(message : types.Message):
    if message.from_user.id == id_admin:
        await FSMAdmin.photo.set()
        await message.reply('Загрузи фото')

#Выход из состояний
# @dp.message_handler(state='*', commands=['Отмена'])
# @dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    if message.from_user.id == id_admin:
        current_state = await state.get_state()
        if current_state is None:
            return
        await state.finish()
        await message.reply('Запись отменена')

#Первый ответ от пользователя
# @dp.message_handler(content_type=['photo'], state=FSMAdmin.photo)
async def load_photo(message: types.Message, state:FSMContext):
    if message.from_user.id == id_admin:
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
        await FSMAdmin.next()
        await message.reply('Название блюда')

#Второй ответ от пользователя
# @dp.message_handler(state=FSMAdmin.name)
async def load_name(message: types.Message, state: FSMContext):
    if message.from_user.id == id_admin:
        async with state.proxy() as data:
            data['name'] = message.text
        await FSMAdmin.next()
        await message.reply('Введите описание')

#Третий ответ от пользователя
# @dp.message_handler(state=FSMAdmin.description)
async def load_description(message: types.Message, state: FSMContext):
    if message.from_user.id == id_admin:
        async with state.proxy() as data:
            data['description'] = message.text
        await FSMAdmin.next()
        await message.reply('Укажите цену')

#Четвертый ответ от пользователя и использование полученных данных
# @dp.message_handler(state=FSMAdmin.price)
async def load_price(message: types.Message, state: FSMContext):
    if message.from_user.id == id_admin:
        async with state.proxy() as data:
            data['price'] = float(message.text)
        await sqlite_db.sql_add_command(state)
        await state.finish()

# @dp.callback_query_handler(lambda x: x.data and x.data.startswith('del '))
async def del_callback_run(callback_query: types.callback_query):
    await sqlite_db.sql_delete_command(callback_query.data.replace('del ', ''))
    await callback_query.answer(text=f'{callback_query.data.replace("del ", "")} удалена', show_alert=True)

# @dp.message_handler(commands='Удалить')
async def delete_item(message : types.Message):
    if message.from_user.id == id_admin:
        read = await sqlite_db.sql_read2()
        for item in read:
            await bot.send_photo(message.from_user.id, item[0], f'{item[1]}\nОписание: {item[2]}\nЦена {item[-1]}')
            await bot.send_message(message.from_user.id, text='^^^', reply_markup=InlineKeyboardMarkup().\
                add(InlineKeyboardButton(f'Удалить {item[1]}', callback_data=f'del {item[1]}')))

#Регистрируем хендлеры
def register_handlers_admin(dp : Dispatcher):
    dp.register_message_handler(cm_start, commands=['Загрузить'], state=None)
    dp.register_message_handler(delete_item, commands='Удалить')
    dp.register_callback_query_handler(del_callback_run, lambda x: x.data and x.data.startswith('del '))
    dp.register_message_handler(cancel_handler, Text(equals='отмена', ignore_case=True), state='*')
    dp.register_message_handler(make_change_command, commands=['moder'], is_chat_admin=True)
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)
    dp.register_message_handler(load_name, state=FSMAdmin.name)
    dp.register_message_handler(load_description, state=FSMAdmin.description)
    dp.register_message_handler(load_price, state=FSMAdmin.price)
    dp.register_message_handler(cancel_handler, state='*', commands=['отмена'])
    