from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Start keyboard with web app button for ordering"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Buyurtma berish", web_app=WebAppInfo(url="https://my-popays.vercel.app/"))],
            [KeyboardButton(text="📋 Mening buyurtmalarim"), KeyboardButton(text="ℹ️ Biz haqimizda")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Buyurtma berish uchun tugmani bosing"
    )
    return keyboard

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Buyurtma berish", web_app=WebAppInfo(url="https://my-popays.vercel.app/"))],
            [KeyboardButton(text="📋 Mening buyurtmalarim"), KeyboardButton(text="ℹ️ Biz haqimizda")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Buyurtma berish uchun tugmani bosing"
    )
    return keyboard

def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Back button keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_order_approval_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Inline keyboard for order approval with Accept/Reject buttons"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_order_{order_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_order_{order_id}")
            ]
        ]
    )
    return keyboard