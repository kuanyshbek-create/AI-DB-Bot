"""
Telegram-бот: принимает фото, имя-фамилию и регалии, генерирует баннер по шаблону
и отправляет готовую картинку в ответ.

Запуск: python bot.py
Токен берётся из переменной окружения BOT_TOKEN (см. .env / .env.example).
"""

import asyncio
import logging
import os
import tempfile

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from dotenv import load_dotenv

import config
from image_gen import generate_banner

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class BannerForm(StatesGroup):
    waiting_photo = State()
    waiting_name = State()
    waiting_credentials = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BannerForm.waiting_photo)
    await message.answer(
        "Привет! Я сделаю для вас баннер.\n\n"
        "Шаг 1 из 3. Пришлите, пожалуйста, фотографию (как фото, не файлом)."
    )


@router.message(BannerForm.waiting_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    # Берём фото в максимальном разрешении
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    await state.set_state(BannerForm.waiting_name)
    await message.answer("Шаг 2 из 3. Введите имя и фамилию (например: Асан Асанов).")


@router.message(BannerForm.waiting_photo)
async def handle_photo_invalid(message: Message):
    await message.answer("Пожалуйста, пришлите именно фотографию (как изображение, а не документ/файл).")


@router.message(BannerForm.waiting_name, F.text)
async def handle_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(BannerForm.waiting_credentials)
    await message.answer(
        "Шаг 3 из 3. Введите регалии/должность (например: Кандидат медицинских наук, врач-кардиолог)."
    )


@router.message(BannerForm.waiting_name)
async def handle_name_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте имя и фамилию текстом.")


@router.message(BannerForm.waiting_credentials, F.text)
async def handle_credentials(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    full_name = data.get("full_name", "")
    credentials = message.text.strip()
    photo_file_id = data.get("photo_file_id")

    await message.answer("Готовлю баннер, подождите несколько секунд...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        user_photo_path = os.path.join(tmp_dir, "user_photo.jpg")
        output_path = os.path.join(tmp_dir, "banner.png")

        file = await bot.get_file(photo_file_id)
        await bot.download_file(file.file_path, destination=user_photo_path)

        try:
            generate_banner(
                template_path=config.TEMPLATE_PATH,
                user_photo_path=user_photo_path,
                full_name=full_name,
                credentials=credentials,
                output_path=output_path,
            )
        except FileNotFoundError:
            await message.answer(
                "Не найден файл шаблона баннера. Убедитесь, что он лежит по пути "
                f"'{config.TEMPLATE_PATH}' относительно папки с ботом."
            )
            await state.clear()
            return
        except Exception:
            logger.exception("Ошибка при генерации баннера")
            await message.answer("Что-то пошло не так при создании баннера. Попробуйте ещё раз командой /start.")
            await state.clear()
            return

        from aiogram.types import FSInputFile

        await message.answer_photo(FSInputFile(output_path), caption="Готово! Вот ваш баннер.")

    await state.clear()


@router.message(BannerForm.waiting_credentials)
async def handle_credentials_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте регалии/должность текстом.")


@router.message()
async def handle_fallback(message: Message):
    await message.answer("Чтобы начать заново, отправьте команду /start.")


async def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "Не найден BOT_TOKEN. Скопируйте .env.example в .env и вставьте туда токен от @BotFather."
        )

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Бот запущен, ожидаю сообщения...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
