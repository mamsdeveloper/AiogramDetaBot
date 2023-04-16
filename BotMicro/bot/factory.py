import asyncio
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.utils.callback_answer import CallbackAnswerMiddleware
from aiogram_deta.storage import DefaultKeyBuilder, DetaStorage
from deta import Deta

from bot.handlers import router as root_router
from bot.middlewares.logging import LoggingMiddleware


def get_webhook_secret() -> str:
    return getenv('DETA_SPACE_APP_MICRO_NAME', '') + getenv('DETA_PROJECT_KEY', '')[:4]


def create_bot(token: str) -> tuple[Bot, str]:
    bot = Bot(token, parse_mode='HTML')

    webhook_url = getenv('DETA_SPACE_APP_HOSTNAME', '') + '/webhook'
    webhook_secret = get_webhook_secret()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(bot.set_webhook(url=webhook_url, secret_token=webhook_secret))

    return bot, webhook_secret


def create_dispatcher(deta: Deta) -> Dispatcher:
    base = deta.AsyncBase('fsm')  # type: ignore
    storage = DetaStorage(base, DefaultKeyBuilder(with_destiny=True))  # type: ignore

    dispatcher = Dispatcher(storage=storage)

    dispatcher.include_router(root_router)
    dispatcher.callback_query.middleware(CallbackAnswerMiddleware())

    if getenv('ENABLE_EVENTS_LOGS') == 'True':
        expire_after_str = getenv('EVENTS_LOGS_EXPIRE_AFTER')
        if expire_after_str is None or expire_after_str == '':
            expire_after = None
        else:
            expire_after = int(expire_after_str)
            
        dispatcher.update.middleware(LoggingMiddleware(expire_after))
        
    return dispatcher
