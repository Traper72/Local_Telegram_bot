from aiogram import Bot
from aiogram.dispatcher import Dispatcher
import os
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()

bot = Bot(token=os.getenv('token'))
dp = Dispatcher(bot, storage=storage)

support_ids = ["ID_ADMIN",]