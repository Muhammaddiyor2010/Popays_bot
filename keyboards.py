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

def get_order_approval_keyboard(order_id=None) -> InlineKeyboardMarkup:
    """Inline keyboard for order approval with Accept/Reject buttons"""
    # Use order_id in callback data if provided, otherwise use generic callbacks
    if order_id:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Qabul qilish", callback_data=f"accept_order_{order_id}"),
                    InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_order_{order_id}")
                ]
            ]
        )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="confirm_order"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")
                ]
            ]
        )
    return keyboard

def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with location sharing button"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Manzil yuborish", request_location=True)],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_admin_pagination_keyboard(current_page: int, total_orders: int, orders_per_page: int) -> InlineKeyboardMarkup:
    """Create pagination keyboard for admin panel"""
    total_pages = (total_orders + orders_per_page - 1) // orders_per_page
    keyboard_buttons = []
    
    # Add navigation buttons
    if current_page > 1:
        keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"admin_page_{current_page - 1}")])
    
    if current_page < total_pages:
        keyboard_buttons.append([InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"admin_page_{current_page + 1}")])
    
    # Add main menu button
    keyboard_buttons.append([InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="admin_main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)