from sys import exc_info
from unittest.mock import call
from xml.etree.ElementTree import register_namespace
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.filters import Command
from create_bot import dp, bot, support_ids
from keyboards.client_kb import kb_client
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import sqlite_db
import random


# @dp.message_handler(commands=['start', 'help'])
async def command_start(message : types.Message):
    try:
        await bot.send_message(message.from_user.id, 'Приветствую, чем могу помочь?', reply_markup=kb_client)
    except:
        await message.reply('Обратитесь к боту в ЛС\nhttps://t.me/Rickroll_shop_bot')

support_callback = CallbackData("ask_support", "messages", "user_id", "as_user")
cancel_support_callback = CallbackData("cancel_support", "user_id")

async def ask_support(message: types.Message):
    text = "Хотите написать сообщение техподдержке? Нажмите на кнопку ниже!"
    keyboard = await support_keyboard(messages="one")
    await message.answer(text, reply_markup=keyboard)

async def send_to_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.answer()
    user_id = int(callback_data.get("user_id"))

    await call.message.answer("Опишите вашу проблему")
    await state.set_state("wait_for_support_message")
    await state.update_data(second_id=user_id)

async def get_support_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    second_id = data.get("second_id")

    await bot.send_message(second_id,
                           f"Вам письмо! Вы можете ответить нажав на кнопку ниже")
    keyboard = await support_keyboard(messages="one", user_id=message.from_user.id)
    await message.copy_to(second_id, reply_markup=keyboard)

    await message.answer("Вы отправили это сообщение!")
    await state.reset_state()

async def check_support_available(support_id):
    state = dp.current_state(chat=support_id, user=support_id)
    state_str = str(
        await state.get_state()
    )
    if state_str == "in_support":
        return
    else:
        return support_id

async def get_support_manager():
    for support_id in support_ids:
        support_id = await check_support_available(support_id)
        if support_id:
            return support_id
    else:
        return 

async def support_keyboard(messages, user_id=None):
    if user_id:
        contact_id = int(user_id)
        as_user = "no"
        text = "Ответить пользователю"
    else:
        contact_id = await get_support_manager()
        as_user = "yes"
        if messages == "many" and contact_id is None:
            return False
        elif messages == "one" and contact_id is None:
            contact_id = random.choice(support_ids)
        if messages == "one":
            text = "Написать 1 сообщение в техподдержку"
        else:
            text = "Написать оператору"
    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            text = text,
            callback_data=support_callback.new(
                messages = messages,
                user_id = contact_id,
                as_user = as_user
            )
        )
    )
        
    if messages=="many":
        keyboard.add(
        InlineKeyboardButton(
            text="Завершить сеанс",
            callback_data=cancel_support_callback.new(
                user_id = contact_id
            )
        )
    )
    return keyboard

def cancel_support(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text = "Завершить сеанс",
                    callback_data = cancel_support_callback.new(
                        user_id = user_id
                    )
                )
            ]
        ]
    )

async def ask_support_call(message: types.Message):
    text = "Хотите связаться с оператором?"
    keyboard = await support_keyboard(messages="many")
    await message.answer(text, reply_markup=keyboard)

async def send_to_support_call(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    await call.message.edit_text("Вы обратились в техподдержку. Ждем ответа от оператора")

    user_id = int(callback_data.get("user_id"))
    if not await check_support_available(user_id):
        support_id = await get_support_manager()
    else:
        support_id = user_id
    if not support_id:
        await call.message.edit_text("К сожалению, сейчас нет свободных операторов. Попробуйте позже.")
        await state.reset_state()
        return
    await state.set_state("wait_in_support")
    await state.update_data(second_id = support_id)
    keyboard = await support_keyboard(messages="many", user_id = call.from_user.id)
    await bot.send_message(support_id, f'С вами хочет связаться пользователь {call.from_user.full_name}', reply_markup=keyboard)

async def answer_to_support_call(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    second_id = int(callback_data.get("user_id"))
    user_state = dp.current_state(user=second_id, chat=second_id)

    if str(await user_state.get_state()) != "wait_in_support":
        await call.message.edit_text("К сожалению, пользователь уже передумал.")
        return
    await state.set_state("in_support")
    await user_state.set_state("in_support")

    await state.update_data(second_id = second_id)

    keyboard = cancel_support(second_id)
    keyboard_second_user = cancel_support(call.from_user.id)

    await call.message.edit_text("Вы на связи с пользователем! Чтобы завершить общение нажмите на кнопку.", 
                                reply_markup=keyboard)
    await bot.send_message(second_id, 
                        "Техподдержка на связи! Можете писать сюда свое сообщение. Чтобы завершить общение нажмите на кнопку.", 
                        reply_markup=keyboard_second_user)

async def not_supported(message: types.Message, state: FSMContext):
    data = await state.get_data()
    second_id = data.get("second_id")

    keyboard = cancel_support(second_id)
    await message.answer("Дождитесь ответа от оператор или отмените сеанс", reply_markup=keyboard)

async def exit_support(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    user_id = int(callback_data.get("user_id"))
    second_state = dp.current_state(user = user_id, chat= user_id)

    if await second_state.get_state() is not None:
        data_second = await second_state.get_data()
        second_id = data_second.get("second_id")
        if int(second_id) == call.from_user.id:
            await second_state.reset_state()
            await bot.send_message(user_id, "Пользователь завершил сеанс техподдержки")
    await call.message.edit_text("Вы завершили сеанс")
    await state.reset_state()


async def select_categories(message : types.Message):
    await bot.send_message(message.from_user.id, 'Выберите категорию вопроса')
    read = await sqlite_db.sql_read_categories()
    for item in read:
        await bot.send_message(message.from_user.id, f'{item[1]}', reply_markup=InlineKeyboardMarkup().\
            add(InlineKeyboardButton(f'Выбрать категорию', callback_data=f'cat {item[0]}')))

async def cat_callback_run(callback_query: types.CallbackQuery):
    await bot.send_message(callback_query.from_user.id, 'Выберите вопрос')
    read = await sqlite_db.sql_read_problems(callback_query.data.replace('cat ', ''))
    # try:
    for item in read:
        await bot.send_message(callback_query.from_user.id, f'{item[2]}', reply_markup=InlineKeyboardMarkup().\
            add(InlineKeyboardButton(text='Выбрать вопрос', callback_data=f'problem {item[0]}')))
    # except:
    #     await bot.send_message(callback_query.from_user.id, text='Не удалось загрузить вопросы')
    await callback_query.answer()

async def problem_callback_run(callback_query: types.callback_query):
    await bot.send_message(callback_query.from_user.id, 'Решение данного вопроса:')
    read = await sqlite_db.sql_read_decision(callback_query.data.replace('problem ', ''))
    await bot.send_message(callback_query.from_user.id, read[0])
    await callback_query.answer()
    

def register_handlers_client(dp : Dispatcher):
    dp.register_message_handler(command_start, commands=['start', 'help'])
    dp.register_message_handler(select_categories, commands=['Помощь'])
    dp.register_message_handler(ask_support_call, Command("Связаться_с_оператором"))
    dp.register_message_handler(ask_support, Command("Письмо_в_техподдержку"))
    dp.register_callback_query_handler(send_to_support, support_callback.filter(messages="one"))
    dp.register_message_handler(get_support_message, state="wait_for_support_message", content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(send_to_support_call, support_callback.filter(messages="many", as_user="yes"))
    dp.register_callback_query_handler(answer_to_support_call, support_callback.filter(messages="many", as_user="no"))
    dp.register_message_handler(not_supported, state="wait_in_support", content_types=types.ContentTypes.ANY)
    dp.register_callback_query_handler(exit_support, cancel_support_callback.filter(), state=["in_support", "wait_in_support", None])
    dp.register_callback_query_handler(cat_callback_run, lambda x: x.data and x.data.startswith('cat '))
    dp.register_callback_query_handler(problem_callback_run, lambda x: x.data and x.data.startswith('problem '))