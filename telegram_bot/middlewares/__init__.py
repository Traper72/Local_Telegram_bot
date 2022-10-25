from aiogram import Dispatcher
from create_bot import dp
from .support_middlware import SupportMiddleware

if __name__ == "middleware":
    dp.middleware.setup(SupportMiddleware())