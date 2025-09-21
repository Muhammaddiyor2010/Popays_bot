from aiogram import Router, F
from aiogram.types import Message, WebAppData, CallbackQuery
from aiogram.filters import Command
import uuid
import json

from config import BOT_NAME, BOT_DESCRIPTION, RESTAURANT_NAME, RESTOURAND_FILIAL1, RESTOURAND_FILIAL2, RESTAURANT_PHONE1, RESTAURANT_PHONE2, RESTAURANT_WORKING_HOURS, ORDER_CHANNEL_ID, DEREZLIK_CHANNEL_ID, ADMIN_ID
from keyboards import get_start_keyboard, get_main_menu_keyboard, get_back_keyboard, get_order_approval_keyboard, get_admin_pagination_keyboard
from database import db
from utils import calculate_delivery_fee, format_delivery_info

# Create router
router = Router()

# Admin password
ADMIN_PASSWORD = "202420"

# Track users waiting for admin password
waiting_for_admin_password = set()

# Track users waiting for broadcast message
waiting_for_broadcast_message = set()

def get_order_channel_id(branch_name):
    """Determine which channel to send the order to based on branch name"""
    if not branch_name:
        return ORDER_CHANNEL_ID  # Default to Kosmonavt channel
    
    branch_lower = branch_name.lower()
    
    # Check if it's Derezlik branch
    if "derezlik" in branch_lower or "derezli" in branch_lower:
        return DEREZLIK_CHANNEL_ID
    
    # Default to Kosmonavt channel for all other cases
    return ORDER_CHANNEL_ID

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command - show main menu with web app button"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    welcome_text = f"""
🎉 <b>Xush kelibsiz, {first_name}!</b>

🍕 <b>{BOT_NAME}</b>
<i>{BOT_DESCRIPTION}</i>

🏪 <b>{RESTAURANT_NAME}</b>
📍 <i>{RESTOURAND_FILIAL1}</i>
📍 <i>{RESTOURAND_FILIAL2}</i>
📞 <i>{RESTAURANT_PHONE1}</i>
📞 <i>{RESTAURANT_PHONE2}</i>
🕐 <i>{RESTAURANT_WORKING_HOURS}</i>

🛒 <b>Buyurtma berish uchun quyidagi tugmani bosing:</b>
🌐 U sizni POPAYS web sahifasiga olib boradi
🍔 Taomlarni ko'rish va tanlash
🚚 Tez yetkazib berish
"""
    
    await message.answer(welcome_text, reply_markup=get_start_keyboard())

@router.message(Command("myorders"))
async def cmd_myorders(message: Message):
    """Handle /myorders command - show user's order history"""
    await my_orders_handler(message)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command - ask for password first"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id != ADMIN_ID:
        # Log unauthorized admin access attempt
        db.log_admin_access(
            user_id=user_id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            action="unauthorized_admin_access_attempt",
            details=f"User {user_id} tried to access admin panel"
        )
        await message.answer(
            "❌ Siz admin emassiz! Bu buyruq faqat admin uchun.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Log admin access attempt
    db.log_admin_access(
        user_id=user_id,
        username=message.from_user.username or '',
        first_name=message.from_user.first_name or '',
        action="admin_access_requested",
        details="Admin requested access to admin panel"
    )
    
    # Ask for password
    waiting_for_admin_password.add(user_id)
    await message.answer(
        "🔐 <b>Admin panelga kirish</b>\n\n"
        "Parolni kiriting:",
        reply_markup=get_back_keyboard()
    )

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Handle /broadcast command - send message to all users"""
    user_id = message.from_user.id
    
    # Check if user is admin
    if user_id != ADMIN_ID:
        # Log unauthorized broadcast attempt
        db.log_admin_access(
            user_id=user_id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            action="unauthorized_broadcast_attempt",
            details=f"User {user_id} tried to broadcast message"
        )
        await message.answer(
            "❌ Siz admin emassiz! Bu buyruq faqat admin uchun.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Log broadcast attempt
    db.log_admin_access(
        user_id=user_id,
        username=message.from_user.username or '',
        first_name=message.from_user.first_name or '',
        action="broadcast_requested",
        details="Admin requested to broadcast message"
    )
    
    # Ask for broadcast message
    waiting_for_broadcast_message.add(user_id)
    await message.answer(
        "📢 <b>Barcha foydalanuvchilarga xabar yuborish</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni yozing:",
        reply_markup=get_back_keyboard()
    )

async def broadcast_message_to_all_users(bot, message_text: str, admin_user_id: int) -> dict:
    """Send broadcast message to all users"""
    try:
        # Get all users from database
        users = db.get_all_users_for_broadcast()
        
        if not users:
            return {
                'success': False,
                'message': 'Foydalanuvchilar topilmadi!',
                'sent': 0,
                'failed': 0
            }
        
        sent_count = 0
        failed_count = 0
        failed_users = []
        
        # Log broadcast start
        db.log_admin_access(
            user_id=admin_user_id,
            username='',
            first_name='',
            action="broadcast_started",
            details=f"Broadcasting to {len(users)} users: {message_text[:100]}..."
        )
        
        # Send message to each user
        for user in users:
            try:
                user_id = user['user_id']
                await bot.send_message(
                    chat_id=user_id,
                    text=message_text,
                    parse_mode="HTML"
                )
                sent_count += 1
                
                # Small delay to avoid rate limiting
                import asyncio
                await asyncio.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                failed_users.append({
                    'user_id': user_id,
                    'username': user.get('username', 'N/A'),
                    'error': str(e)
                })
                print(f"❌ Failed to send broadcast to user {user_id}: {e}")
        
        # Log broadcast completion
        db.log_admin_access(
            user_id=admin_user_id,
            username='',
            first_name='',
            action="broadcast_completed",
            details=f"Sent: {sent_count}, Failed: {failed_count}"
        )
        
        return {
            'success': True,
            'message': f'Xabar yuborildi: {sent_count} ta foydalanuvchiga',
            'sent': sent_count,
            'failed': failed_count,
            'failed_users': failed_users
        }
        
    except Exception as e:
        print(f"❌ Error in broadcast_message_to_all_users: {e}")
        return {
            'success': False,
            'message': f'Xabar yuborishda xatolik: {str(e)}',
            'sent': 0,
            'failed': 0
        }

async def show_admin_panel(message: Message, page: int = 1):
    """Show admin panel after password verification"""
    try:
        # Log successful admin panel access
        db.log_admin_access(
            user_id=message.from_user.id,
            username=message.from_user.username or '',
            first_name=message.from_user.first_name or '',
            action="admin_panel_accessed",
            details=f"Admin panel accessed, page {page}"
        )
        
        # Get statistics
        stats = db.get_statistics()
        
        # Get recent orders with pagination
        orders_per_page = 5
        offset = (page - 1) * orders_per_page
        recent_orders = db.get_recent_orders_admin(limit=orders_per_page, offset=offset)
        
        # Get total orders count for pagination
        total_orders = db.get_total_orders_count()
        
        # Get users with orders
        users_with_orders = db.get_all_users_with_orders(limit=20)
        
        # Format admin panel message
        admin_message = f"""
<b>ADMIN PANEL</b>

<b>Umumiy statistika:</b>
• Jami buyurtmalar: {stats.get('total_orders', 0)} ta
• Jami daromad: {stats.get('total_revenue', 0):,.0f} so'm
• Jami lokatsiyalar: {stats.get('total_locations', 0)} ta

<b>Buyurtmalar holati bo'yicha:</b>
"""
        
        # Add order status breakdown
        orders_by_status = stats.get('orders_by_status', {})
        status_emojis = {
            'pending': '[Kutilmoqda]',
            'accepted': '[Qabul qilingan]', 
            'rejected': '[Rad etilgan]',
            'completed': '[Tugallangan]',
            'cancelled': '[Bekor qilingan]'
        }
        
        status_texts = {
            'pending': 'Kutilmoqda',
            'accepted': 'Qabul qilingan',
            'rejected': 'Rad etilgan', 
            'completed': 'Tugallangan',
            'cancelled': 'Bekor qilingan'
        }
        
        for status, count in orders_by_status.items():
            emoji = status_emojis.get(status, '[Noma\'lum]')
            text = status_texts.get(status, status)
            admin_message += f"• {emoji} {text}: {count} ta\n"
        
        admin_message += f"\n<b>Foydalanuvchilar ({len(users_with_orders)} ta):</b>\n"
        
        # Add users list
        for i, user in enumerate(users_with_orders[:10], 1):
            username = user['username'] if user['username'] != 'N/A' else 'N/A'
            first_name = user['first_name'] if user['first_name'] != 'N/A' else 'N/A'
            last_order_date = user.get('last_order_date', 'N/A')
            if last_order_date and last_order_date != 'N/A':
                last_order_date = str(last_order_date)[:16]
            
            admin_message += f"""
<b>{i}. @{username}</b> ({first_name})
ID: {user['user_id']}
Buyurtmalar: {user['order_count']} ta
Jami sarflangan: {user['total_spent']:,.0f} so'm
Oxirgi buyurtma: {last_order_date}
"""
        
        if len(users_with_orders) > 10:
            admin_message += f"\n... va yana {len(users_with_orders) - 10} ta foydalanuvchi"
        
        admin_message += f"\n\n<b>Buyurtmalar (sahifa {page}):</b>\n"
        
        # Add recent orders
        for i, order in enumerate(recent_orders, 1):
            status_emoji = status_emojis.get(order['status'], '[Noma\'lum]')
            customer_name = order['customer_name'] if order['customer_name'] != 'N/A' else 'N/A'
            username = order['username'] if order['username'] != 'N/A' else 'N/A'
            created_at = order.get('created_at', 'N/A')
            if created_at and created_at != 'N/A':
                created_at = str(created_at)[:16]
            
            admin_message += f"""
<b>{i}. Buyurtma #{order['id']}</b> {status_emoji}
Mijoz: {customer_name} (@{username})
Summa: {order['total_amount']:,.0f} so'm
Sana: {created_at}
"""
        
        # Create pagination keyboard
        keyboard = get_admin_pagination_keyboard(page, total_orders, orders_per_page)
        
        await message.answer(admin_message, reply_markup=keyboard)
        
    except Exception as e:
        print(f"❌ Error in admin panel: {e}")
        await message.answer(
            "❌ Admin panelda xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(F.text == "🛒 Buyurtma berish")
async def order_handler(message: Message):
    """Handle order button - show web app info"""
    await message.answer(
        "🛒 <b>Buyurtma berish uchun yuqoridagi tugmani bosing!</b> U sizni POPAYS web sahifasiga olib boradi.\n\n"
        "🌐 <b>Web sahifada:</b>\n"
        "• Taomlarni ko'rish va tanlash\n"
        "• Savatga qo'shish\n"
        "• Buyurtma berish\n"
        "• To'lov qilish\n\n"
        "🚀 <b>Tez va qulay buyurtma berish!</b>",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(F.web_app_data)
async def web_app_handler(message: Message):
    """Handle web app data from POPAYS website"""
    try:
        # Parse web app data
        web_app_data = message.web_app_data
        data = web_app_data.data
        
        print(f"📥 Received web app data: {data}")
        print(f"📥 Data length: {len(data)} characters")
        
        # Parse JSON data
        import json
        try:
            order_data = json.loads(data)
            print(f"✅ JSON parsed successfully. Order type: {order_data.get('type', 'unknown')}")
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON parsing error: {json_error}")
            print(f"❌ Raw data: {data[:200]}...")  # Show first 200 chars
            try:
                await message.answer(
                    "❌ <b>Buyurtma ma'lumotlari noto'g'ri formatda!</b>\n\n"
                    "Iltimos, qaytadan urinib ko'ring yoki @popays_support ga murojaat qiling.",
                    reply_markup=get_main_menu_keyboard()
                )
            except Exception as json_msg_error:
                print(f"❌ Error sending JSON error message: {json_msg_error}")
            return
        
        # Check if this is location_complete, mapData or order data
        if order_data.get('type') == 'location_complete':
            # This is location_complete structure
            coordinates = order_data.get('coordinates', {})
            address = order_data.get('address', 'N/A')
            maps = order_data.get('maps', {})
            
            
            # Check if maps links are available
            has_google = bool(maps.get('google'))
            has_yandex = bool(maps.get('yandex'))
            has_osm = bool(maps.get('osm'))
            
            # If no map links available, reject the order
            if not (has_google or has_yandex or has_osm):
                error_message = """
❌ <b>BUYURTMA QABUL QILINMADI!</b>

🗺️ <b>Sabab:</b> Xarita linklari topilmadi!

📍 <b>Kerakli ma'lumotlar:</b>
• Google Maps linki
• Yandex Maps linki  
• OpenStreetMap linki

🔄 <b>Qanday qilish kerak:</b>
1. Web sahifada lokatsiyangizni qayta belgilang
2. Xarita linklari avtomatik yaratilishini kuting
3. Buyurtmani qayta yuboring

📞 <b>Yordam kerak bo'lsa:</b> @popays_support
"""
                try:
                    await message.answer(error_message, reply_markup=get_main_menu_keyboard())
                except Exception as map_error_msg:
                    print(f"❌ Error sending map error message: {map_error_msg}")
                print(f"❌ Buyurtma rad etildi - xarita linklari yo'q: {order_data}")
                return
            
            # Check if coordinates are valid
            if not coordinates.get('latitude') or not coordinates.get('longitude'):
                error_message = """
❌ <b>BUYURTMA QABUL QILINMADI!</b>

📍 <b>Sabab:</b> Koordinatalar noto'g'ri!

🌍 <b>Kerakli ma'lumotlar:</b>
• Kenglik (latitude)
• Uzunlik (longitude)

🔄 <b>Qanday qilish kerak:</b>
1. Web sahifada lokatsiyangizni qayta belgilang
2. GPS yoqilganligini tekshiring
3. Lokatsiya ruxsatini bering
4. Buyurtmani qayta yuboring

📞 <b>Yordam kerak bo'lsa:</b> @popays_support
"""
                try:
                    await message.answer(error_message, reply_markup=get_main_menu_keyboard())
                except Exception as coord_error_msg:
                    print(f"❌ Error sending coordinate error message: {coord_error_msg}")
                print(f"❌ Buyurtma rad etildi - koordinatalar noto'g'ri: {coordinates}")
                return
            
            # Save location to database
            try:
                location_id = db.create_location(
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    first_name=message.from_user.first_name or '',
                    location_data=order_data
                )
                print(f"✅ Location saved to database with ID: {location_id}")
            except Exception as db_error:
                print(f"❌ Error saving location to database: {db_error}")
                location_id = str(uuid.uuid4())[:8]  # Fallback ID
            
            # Format location message
            location_message = f"""
🗺️ <b>YANGI LOKATSIYA</b> 🗺️

📍 <b>Lokatsiya:</b> {address}

🌍 <b>Koordinatalar:</b>
• Kenglik: {coordinates.get('latitude', 'N/A')}
• Uzunlik: {coordinates.get('longitude', 'N/A')}
• Aniqlik: {coordinates.get('accuracy', 'N/A')}m

🗺️ <b>Xarita linklari:</b>
"""
            
            if maps.get('google'):
                location_message += f"• Google Maps: {maps['google']}\n"
            if maps.get('yandex'):
                location_message += f"• Yandex Maps: {maps['yandex']}\n"
            if maps.get('osm'):
                location_message += f"• OpenStreetMap: {maps['osm']}\n"
            
            location_message += f"""
👤 <b>Foydalanuvchi:</b> @{message.from_user.username or 'N/A'}
🆔 <b>User ID:</b> {message.from_user.id}
📱 <b>Ism:</b> {message.from_user.first_name or 'N/A'}
⏰ <b>Vaqt:</b> {order_data.get('timestamp', 'N/A')}
🆔 <b>Location ID:</b> {location_id}

🚚 <b>Yetkazib berish uchun tayyor!</b>
"""
            
            # Send location data to channel (default to Kosmonavt for location-only messages)
            try:
                await message.bot.send_message(
                    ORDER_CHANNEL_ID, 
                    location_message, 
                    reply_markup=get_order_approval_keyboard()
                )
                print(f"✅ Lokatsiya ma'lumotlari kanalga yuborildi: {ORDER_CHANNEL_ID} (Kosmonavt filiali) - Location ID: {location_id}")
                
                # Send location as Telegram location
                if coordinates.get('latitude') and coordinates.get('longitude'):
                    try:
                        await message.bot.send_location(
                            chat_id=ORDER_CHANNEL_ID,
                            latitude=coordinates.get('latitude'),
                            longitude=coordinates.get('longitude')
                        )
                        print(f"✅ Lokatsiya kanalga yuborildi: {coordinates.get('latitude')}, {coordinates.get('longitude')} (Kosmonavt filiali)")
                    except Exception as loc_error:
                        print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                
            # Send confirmation to user
            try:
                await message.answer(
                    "🗺️ <b>Lokatsiya ma'lumotlari qabul qilindi va kanalga yuborildi!</b>",
                    reply_markup=get_main_menu_keyboard()
                )
                print(f"✅ Location confirmation sent to user")
            except Exception as loc_msg_error:
                print(f"❌ Error sending location confirmation: {loc_msg_error}")
            
        elif order_data.get('mapData') and not order_data.get('type'):
            # This is mapData structure
            map_data = order_data.get('mapData', {})
            customer = map_data.get('customer', {})
            
            
            # Save map data to database as location
            try:
                # Convert mapData to location format for database
                location_data = {
                    'coordinates': map_data.get('coordinates', {}),
                    'address': map_data.get('address', ''),
                    'maps': map_data.get('mapLinks', {}),
                    'timestamp': map_data.get('timestamp', '')
                }
                
                map_id = db.create_location(
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    first_name=message.from_user.first_name or '',
                    location_data=location_data
                )
                print(f"✅ Map data saved to database with ID: {map_id}")
            except Exception as db_error:
                print(f"❌ Error saving map data to database: {db_error}")
                map_id = str(uuid.uuid4())[:8]  # Fallback ID
            
            # Format map data message
            map_message = f"""
🗺️ <b>XARITA MA'LUMOTLARI</b> 🗺️

👤 <b>Mijoz:</b>
• Ism: {customer.get('name', 'N/A')}
• Telefon: {customer.get('phone', 'N/A')}

📍 <b>Lokatsiya:</b>
• Koordinatalar: {map_data.get('coordinates', {}).get('latitude', 'N/A')}, {map_data.get('coordinates', {}).get('longitude', 'N/A')}
• Aniqlik: {map_data.get('coordinates', {}).get('accuracy', 'N/A')}m
• Vaqt: {map_data.get('timestamp', 'N/A')}

🗺️ <b>Xarita linklari:</b>
"""
            
            map_links = map_data.get('mapLinks', {})
            if map_links.get('google'):
                map_message += f"• Google Maps: {map_links['google']}\n"
            if map_links.get('yandex'):
                map_message += f"• Yandex Maps: {map_links['yandex']}\n"
            if map_links.get('osm'):
                map_message += f"• OpenStreetMap: {map_links['osm']}\n"
            
            if map_data.get('note'):
                map_message += f"\n📝 <b>Izoh:</b> {map_data.get('note')}"
            
            if map_data.get('status'):
                map_message += f"\n📊 <b>Holat:</b> {map_data.get('status')}"
            
            map_message += f"\n🆔 <b>Map ID:</b> {map_id}"
            
            # Send map data to channel (default to Kosmonavt for map-only messages)
            try:
                await message.bot.send_message(
                    ORDER_CHANNEL_ID, 
                    map_message, 
                    reply_markup=get_order_approval_keyboard()
                )
                print(f"✅ Xarita ma'lumotlari kanalga yuborildi: {ORDER_CHANNEL_ID} (Kosmonavt filiali) - Map ID: {map_id}")
                
                # Send location as Telegram location
                coords = map_data.get('coordinates', {})
                if coords.get('latitude') and coords.get('longitude'):
                    try:
                        await message.bot.send_location(
                            chat_id=ORDER_CHANNEL_ID,
                            latitude=coords.get('latitude'),
                            longitude=coords.get('longitude')
                        )
                        print(f"✅ Lokatsiya kanalga yuborildi: {coords.get('latitude')}, {coords.get('longitude')} (Kosmonavt filiali)")
                    except Exception as loc_error:
                        print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                
            # Send confirmation to user
            try:
                await message.answer(
                    "🗺️ <b>Xarita ma'lumotlari qabul qilindi va kanalga yuborildi!</b>",
                    reply_markup=get_main_menu_keyboard()
                )
                print(f"✅ Map data confirmation sent to user")
            except Exception as map_msg_error:
                print(f"❌ Error sending map data confirmation: {map_msg_error}")
            
        elif order_data.get('type') == 'order':
            # This is order data
            print(f"🛒 Processing order data...")
            customer = order_data.get('customer', {})
            items = order_data.get('items', [])
            total = order_data.get('total', 0)
            timestamp = order_data.get('timestamp', '')
            restaurant = order_data.get('restaurant', 'POPAYS')
            map_data = order_data.get('mapData', {})
            
            print(f"📊 Order details: customer={customer.get('name', 'N/A')}, items={len(items)}, total={total}")
            
            # Save order to database
            print(f"💾 Saving order to database...")
            try:
                order_id = db.create_order(
                    user_id=message.from_user.id,
                    username=message.from_user.username or '',
                    first_name=message.from_user.first_name or '',
                    order_data=order_data
                )
                print(f"✅ Order saved to database with ID: {order_id}")
            except Exception as db_error:
                print(f"❌ Error saving order to database: {db_error}")
                print(f"❌ Error type: {type(db_error).__name__}")
                try:
                    await message.answer(
                        "❌ <b>Buyurtma saqlashda xatolik yuz berdi!</b>\n\n"
                        "Iltimos, qaytadan urinib ko'ring yoki @popays_support ga murojaat qiling.",
                        reply_markup=get_main_menu_keyboard()
                    )
                except Exception as db_msg_error:
                    print(f"❌ Error sending database error message: {db_msg_error}")
                return
            
            # Format order message
            order_message = f"""
🆕 <b>YANGI BUYURTMA!</b> 🆕

🏪 <b>Filial:</b> {order_data.get('branch', 'N/A')}

👤 <b>Mijoz ma'lumotlari:</b>
• Ism: {customer.get('name', 'N/A')}
• Telefon: {customer.get('phone', 'N/A')}
• Manzil: {customer.get('location', 'N/A')}
"""
            
            # Add map data and calculate delivery fee if available
            delivery_fee = 0
            delivery_info_text = ""
            if map_data and map_data.get('coordinates'):
                coords = map_data['coordinates']
                map_links = map_data.get('mapLinks', {})
                
                
                # Calculate delivery fee based on coordinates
                try:
                    latitude = coords.get('latitude')
                    longitude = coords.get('longitude')
                    if latitude and longitude:
                        delivery_info = calculate_delivery_fee(latitude, longitude, total)
                        
                        # Check if delivery is available (within 20km)
                        if not delivery_info.get('is_delivery_available', True):
                            # Distance is too far, send error message to user
                            try:
                                await message.answer(
                                    delivery_info['error_message'],
                                    reply_markup=get_main_menu_keyboard()
                                )
                            except Exception as delivery_msg_error:
                                print(f"❌ Error sending delivery error message: {delivery_msg_error}")
                            return
                        
                        delivery_fee = delivery_info['total_delivery_fee']
                        delivery_info_text = format_delivery_info(delivery_info)
                        
                        # Update order with delivery fee
                        db.update_order_location_and_fee(
                            order_id=order_id,
                            latitude=latitude,
                            longitude=longitude,
                            delivery_fee=delivery_fee,
                            nearest_branch=delivery_info['nearest_branch']
                        )
                        
                        print(f"💰 Delivery fee calculated: {delivery_fee} sum")
                        
                except Exception as e:
                    print(f"❌ Error calculating delivery fee: {e}")
                    # Continue without delivery fee if calculation fails
                    delivery_fee = 0
                    delivery_info_text = ""
                
                order_message += f"""
📍 <b>Lokatsiya ma'lumotlari:</b>
• Koordinatalar: {coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}
• Aniqlik: {coords.get('accuracy', 'N/A')}m
"""
                
                # Add delivery fee information
                if delivery_info_text:
                    order_message += f"\n🚚 <b>Yetkazib berish ma'lumotlari:</b>\n{delivery_info_text}\n"
                
                # Add map links
                if map_links:
                    order_message += "\n🗺️ <b>Xarita linklari:</b>\n"
                    if map_links.get('google'):
                        order_message += f"• Google Maps: {map_links['google']}\n"
                    if map_links.get('yandex'):
                        order_message += f"• Yandex Maps: {map_links['yandex']}\n"
                    if map_links.get('osm'):
                        order_message += f"• OpenStreetMap: {map_links['osm']}\n"
            
            # Add items if available
            if items:
                order_message += "\n🍽️ <b>Buyurtma:</b>\n"
                for item in items:
                    name = item.get('name', 'N/A')
                    quantity = item.get('quantity', 1)
                    total = item.get('total', 0)
                    selected_size = item.get('selectedSize', '')
                    
                    # Format item with size if available
                    if selected_size:
                        order_message += f"• {name} ({selected_size}) x{quantity} = {total:,} so'm\n"
                    else:
                        order_message += f"• {name} x{quantity} = {total:,} so'm\n"
            
            # Add total and other info
            if total:
                if delivery_fee > 0:
                    order_message += f"\n💰 <b>Taomlar: {total:,} so'm</b>"
                    order_message += f"\n🚚 <b>Yetkazib berish: {delivery_fee:,} so'm</b>"
                    order_message += f"\n💳 <b>JAMI: {total + delivery_fee:,} so'm</b>"
                else:
                    order_message += f"\n💰 <b>Jami: {total:,} so'm</b>"
            
            order_message += f"\n🏪 <b>Restoran:</b> {restaurant}"
            order_message += f"\n🏢 <b>Filial:</b> {order_data.get('branch', 'N/A')}"
            order_message += f"\n⏰ <b>Vaqt:</b> {timestamp}"
            order_message += f"\n📱 <b>Telegram:</b> @{message.from_user.username or 'N/A'}"
            order_message += f"\n🆔 <b>User ID:</b> {message.from_user.id}"
            order_message += f"\n🆔 <b>Order ID:</b> {order_id}"
            
            # Create short message for user
            customer_name = customer.get('name', 'N/A')
            customer_phone = customer.get('phone', 'N/A')
            
            user_message = f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
            user_message += f"👤 <b>Ism:</b> {customer_name}\n"
            user_message += f"📞 <b>Telefon:</b> {customer_phone}\n\n"
            
            # Add items
            if items:
                user_message += "🍽️ <b>Buyurtma:</b>\n"
                for item in items[:3]:  # Show first 3 items
                    name = item.get('name', 'N/A')
                    quantity = item.get('quantity', 1)
                    selected_size = item.get('selectedSize', '')
                    if selected_size:
                        user_message += f"• {name} ({selected_size}) x{quantity}\n"
                    else:
                        user_message += f"• {name} x{quantity}\n"
                if len(items) > 3:
                    user_message += f"• ... va yana {len(items) - 3} ta\n"
            
            # Add delivery fee
            if delivery_fee > 0:
                user_message += f"\n🚚 <b>Yetkazib berish:</b> {delivery_fee:,} so'm"
            
            # User message removed - only channel gets the order details
            print(f"📤 User confirmation message skipped - only channel notification sent")
            
            # Determine which channel to send the order to based on branch
            target_channel_id = get_order_channel_id(order_data.get('branch', ''))
            channel_name = "Derezlik filiali" if target_channel_id == DEREZLIK_CHANNEL_ID else "Kosmonavt filiali"
            
            # Send detailed order to appropriate channel with inline keyboard
            print(f"📤 Sending order to channel: {target_channel_id} ({channel_name})")
            try:
                await message.bot.send_message(
                    target_channel_id, 
                    order_message, 
                    reply_markup=get_order_approval_keyboard(order_id)
                )
                print(f"✅ Buyurtma kanalga yuborildi: {target_channel_id} ({channel_name}) - Order ID: {order_id}")
                
                # If map data available, also send location
                if map_data:
                    coords = map_data.get('coordinates', {})
                    if coords:
                        lat = coords.get('latitude')
                        lon = coords.get('longitude')
                        
                        if lat and lon:
                            try:
                                # Send location as Telegram location
                                await message.bot.send_location(
                                    chat_id=target_channel_id,
                                    latitude=float(lat),
                                    longitude=float(lon)
                                )
                                print(f"✅ Lokatsiya kanalga yuborildi: {lat}, {lon} ({channel_name})")
                            except Exception as loc_error:
                                print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                # If channel not accessible, send to admin
                try:
                    from config import ADMIN_ID
                    # Add order info to admin message too
                    admin_order_message = order_message
                    await message.bot.send_message(
                        ADMIN_ID, 
                        admin_order_message, 
                        reply_markup=get_order_approval_keyboard()
                    )
                    print(f"✅ Buyurtma admin ga yuborildi: {ADMIN_ID} - Order ID: {order_id}")
                    
                    # Also send location to admin if available
                    if map_data and map_data.get('coordinates'):
                        coords = map_data['coordinates']
                        try:
                            await message.bot.send_location(
                                chat_id=ADMIN_ID,
                                latitude=coords.get('latitude'),
                                longitude=coords.get('longitude')
                            )
                            print(f"✅ Lokatsiya admin ga yuborildi: {coords.get('latitude')}, {coords.get('longitude')}")
                        except Exception as loc_error:
                            print(f"❌ Admin ga lokatsiya yuborishda xatolik: {loc_error}")
                            
                except Exception as admin_error:
                    print(f"❌ Admin ga yuborishda xatolik: {admin_error}")
                    # If even admin notification fails, at least inform the user
                    await message.answer(
                        "⚠️ <b>Buyurtma qabul qilindi, lekin kanalga yuborishda muammo bor!</b>\n\n"
                        "Iltimos, @popays_support ga murojaat qiling.",
                        reply_markup=get_main_menu_keyboard()
                    )
                
        else:
            try:
                await message.answer("❌ <b>Noto'g'ri buyurtma formati!</b>")
            except Exception as format_error:
                print(f"❌ Error sending format error message: {format_error}")
            
    except Exception as e:
        print(f"❌ Web app handler error: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        try:
            await message.answer(
                "❌ <b>Buyurtma qayta ishlashda xatolik yuz berdi!</b>\n\n"
                "Iltimos, qaytadan urinib ko'ring yoki @popays_support ga murojaat qiling.\n\n"
                "🔄 <b>Qayta urinish uchun:</b> /start",
                reply_markup=get_main_menu_keyboard()
            )
        except Exception as main_error_msg:
            print(f"❌ Error sending main error message: {main_error_msg}")
            # Last resort - try to send a very simple message
            try:
                await message.answer("❌ Xatolik yuz berdi. /start ni bosing.")
            except:
                print(f"❌ Complete message sending failure")

@router.message(F.text == "📋 Mening buyurtmalarim")
async def my_orders_handler(message: Message):
    """Handle my orders button - show user's order history"""
    user_id = message.from_user.id
    
    try:
        # Get user's orders from database
        orders = db.get_user_orders(user_id, limit=10)
        
        if not orders:
            await message.answer(
                "📋 <b>Sizda hali buyurtmalar yo'q.</b>\n\n"
                "🛒 Birinchi buyurtmangizni berish uchun yuqoridagi tugmani bosing!",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Format orders message
        orders_text = f"<b>Sizning buyurtmalaringiz</b> ({len(orders)} ta)\n\n"
        
        for i, order in enumerate(orders, 1):
            status_emoji = {
                'pending': '[Kutilmoqda]',
                'accepted': '[Qabul qilingan]',
                'rejected': '[Rad etilgan]',
                'completed': '[Tugallangan]',
                'cancelled': '[Bekor qilingan]'
            }.get(order['status'], '[Noma\'lum]')
            
            status_text = {
                'pending': 'Kutilmoqda',
                'accepted': 'Qabul qilingan',
                'rejected': 'Rad etilgan',
                'completed': 'Tugallangan',
                'cancelled': 'Bekor qilingan'
            }.get(order['status'], order['status'])
            
            # Safe date formatting
            created_at = order.get('created_at', 'N/A')
            if created_at and created_at != 'N/A':
                created_at = str(created_at)[:16]
            
            orders_text += f"<b>{i}. Buyurtma #{order['id']}</b>\n"
            orders_text += f"{status_emoji} <b>Holat:</b> {status_text}\n"
            orders_text += f"<b>Summa:</b> {order['total_amount']:,.0f} so'm\n"
            orders_text += f"<b>Sana:</b> {created_at}\n"
            
            # Add items if available
            if order.get('items'):
                orders_text += "<b>Taomlar:</b>\n"
                for item in order['items'][:3]:  # Show first 3 items
                    size_text = f" ({item['selectedSize']})" if item.get('selectedSize') else ""
                    orders_text += f"• {item['name']}{size_text} x{item['quantity']}\n"
                if len(order['items']) > 3:
                    orders_text += f"• ... va yana {len(order['items']) - 3} ta\n"
            
            orders_text += "\n" + "─" * 30 + "\n\n"
        
        # Add summary
        total_spent = sum(order['total_amount'] for order in orders)
        orders_text += f"<b>Jami:</b> {len(orders)} ta buyurtma\n"
        orders_text += f"<b>Jami sarflangan:</b> {total_spent:,.0f} so'm"
        
        await message.answer(orders_text, reply_markup=get_main_menu_keyboard())
        
    except Exception as e:
        print(f"❌ Error getting user orders: {e}")
        await message.answer(
            "❌ <b>Buyurtmalaringizni olishda xatolik yuz berdi.</b> Iltimos, qayta urinib ko'ring.",
            reply_markup=get_main_menu_keyboard()
        )

@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_handler(message: Message):
    """Handle about us button"""
    about_text = f"""
ℹ️ <b>Biz haqimizda</b>

🏪 <b>{RESTAURANT_NAME}</b>
📍 <i>{RESTOURAND_FILIAL1}</i>
📍 <i>{RESTOURAND_FILIAL2}</i>
📞 <i>{RESTAURANT_PHONE1}</i>
📞 <i>{RESTAURANT_PHONE2}</i>
🕐 <i>{RESTAURANT_WORKING_HOURS}</i>

🍽️ <b>Bizning taomlarimiz:</b>
• Tez va qulay yetkazib berish
• Professional oshpazlar
• 8:00 dan 3:00 gacha xizmat ko'rstatish

🎉 <b>Maxsus imkoniyatlar:</b>
• Buyurtma berib o'z instgaramizga storis qo'ysangiz sovg'a
• Bepul yetkazib berish 3km gacha
"""
    
    await message.answer(about_text, reply_markup=get_main_menu_keyboard())

@router.message(F.text == "🔙 Orqaga")
async def back_handler(message: Message):
    """Handle back button"""
    user_id = message.from_user.id
    
    # Remove from waiting for admin password if they were waiting
    if user_id in waiting_for_admin_password:
        waiting_for_admin_password.remove(user_id)
    
    await cmd_start(message)

@router.message()
async def password_handler(message: Message):
    """Handle password input for admin panel and broadcast messages"""
    user_id = message.from_user.id
    
    # Check if user is waiting for admin password
    if user_id in waiting_for_admin_password:
        # Remove from waiting list
        waiting_for_admin_password.remove(user_id)
        
        # Check password
        if message.text == ADMIN_PASSWORD:
            # Log successful password verification
            db.log_admin_access(
                user_id=user_id,
                username=message.from_user.username or '',
                first_name=message.from_user.first_name or '',
                action="admin_password_verified",
                details="Admin password verified successfully"
            )
            await message.answer("✅ <b>Parol to'g'ri! Admin panelga kirdingiz.</b>")
            await show_admin_panel(message)
        else:
            # Log failed password attempt
            db.log_admin_access(
                user_id=user_id,
                username=message.from_user.username or '',
                first_name=message.from_user.first_name or '',
                action="admin_password_failed",
                details=f"Failed password attempt: {message.text}"
            )
            await message.answer(
                "❌ <b>Noto'g'ri parol!</b> Iltimos, qayta urinib ko'ring.\n\n"
                "Admin panelga kirish uchun /admin buyrug'ini qayta yuboring.",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    # Check if user is waiting for broadcast message
    if user_id in waiting_for_broadcast_message:
        # Remove from waiting list
        waiting_for_broadcast_message.remove(user_id)
        
        # Get the message text
        broadcast_text = message.text
        
        # Send confirmation message
        await message.answer(
            "📢 <b>Xabar yuborilmoqda...</b>\n\n"
            "Iltimos, kuting. Bu biroz vaqt olishi mumkin.",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Send broadcast message to all users
        result = await broadcast_message_to_all_users(
            bot=message.bot,
            message_text=broadcast_text,
            admin_user_id=user_id
        )
        
        # Send result to admin
        if result['success']:
            result_message = f"✅ <b>Xabar muvaffaqiyatli yuborildi!</b>\n\n"
            result_message += f"📤 <b>Yuborildi:</b> {result['sent']} ta foydalanuvchiga\n"
            if result['failed'] > 0:
                result_message += f"❌ <b>Yuborilmadi:</b> {result['failed']} ta foydalanuvchiga\n"
            result_message += f"\n📝 <b>Xabar:</b>\n{broadcast_text}"
        else:
            result_message = f"❌ <b>Xabar yuborishda xatolik!</b>\n\n{result['message']}"
        
        await message.answer(result_message, reply_markup=get_main_menu_keyboard())
        return
    
    # If not waiting for password or broadcast, handle as regular message
    await echo_handler(message)

async def echo_handler(message: Message):
    """Handle all other messages"""
    await message.answer(
        "❓ <b>Tushunarsiz buyruq.</b> Bosh sahifaga qaytish uchun /start ni bosing.",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "confirm_order")
async def confirm_order_callback(callback: CallbackQuery):
    """Handle order confirmation by customer"""
    try:
        user_id = callback.from_user.id
        current_order = db.get_user_current_order(user_id)
        
        if not current_order:
            await callback.answer("❌ Sizda faol buyurtma yo'q!", show_alert=True)
            return
        
        order_id = current_order['id']
        
        # Update order status in database
        try:
            db.update_order_status(order_id, "accepted")
            print(f"✅ Order {order_id} status updated to 'accepted' in database")
        except Exception as db_error:
            print(f"❌ Error updating order status in database: {db_error}")
        
        # Extract customer user ID from the message
        message_text = callback.message.text
        customer_user_id = None
        
        # Look for customer user ID in the message
        import re
        user_id_match = re.search(r'🆔 <b>User ID:</b> (\d+)', message_text)
        if user_id_match:
            customer_user_id = int(user_id_match.group(1))
        
        # Edit the message to show it's accepted
        original_text = callback.message.text
        accepted_text = f"{original_text}\n\n✅ <b>QABUL QILINDI</b> #qabul_qilingan\n👨‍💼 <b>Admin:</b> @{callback.from_user.username or callback.from_user.first_name}"
        
        await callback.message.edit_text(
            accepted_text,
        )
        
        # Send confirmation to customer if user ID found
        if customer_user_id:
            try:
                # Get order details for short message
                order_details = db.get_order(order_id)
                customer_name = order_details.get('customer_name', 'N/A') if order_details else 'N/A'
                customer_phone = order_details.get('customer_phone', 'N/A') if order_details else 'N/A'
                total_amount = order_details.get('total_amount', 0) if order_details else 0
                delivery_fee = order_details.get('delivery_fee', 0) if order_details else 0
                
                # Get ordered products
                items_text = ""
                if order_details and order_details.get('items'):
                    items = order_details['items']
                    for item in items[:3]:  # Show first 3 items
                        size_text = f" ({item.get('selectedSize', '')})" if item.get('selectedSize') else ""
                        items_text += f"• {item.get('name', 'N/A')}{size_text} x{item.get('quantity', 1)}\n"
                    if len(items) > 3:
                        items_text += f"• ... va yana {len(items) - 3} ta\n"
                
                # Create detailed customer message
                customer_message = f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
                customer_message += f"🆔 <b>Buyurtma raqami:</b> #{order_id}\n"
                customer_message += f"👤 <b>Ism:</b> {customer_name}\n"
                customer_message += f"📞 <b>Telefon:</b> {customer_phone}\n\n"
                
                if items_text:
                    customer_message += f"🍽️ <b>Buyurtma:</b>\n{items_text}"
                
                if delivery_fee > 0:
                    customer_message += f"💰 <b>Taomlar:</b> {total_amount:,} so'm\n"
                    customer_message += f"🚚 <b>Yetkazib berish:</b> {delivery_fee:,} so'm\n"
                    customer_message += f"💳 <b>JAMI:</b> {total_amount + delivery_fee:,} so'm"
                else:
                    customer_message += f"💰 <b>Jami:</b> {total_amount:,} so'm"
                
                customer_message += f"\n\n⏰ <b>Buyurtma qabul qilindi!</b>\n"
                customer_message += f"📦 Tez orada tayyorlanadi va yetkazib beriladi.\n"
                customer_message += f"📞 Savollar uchun: @popays_support"
                await callback.bot.send_message(
                    chat_id=customer_user_id,
                    text=customer_message,
                )
                print(f"✅ Customer notification sent to user {customer_user_id} for order {order_id}")
            except Exception as notify_error:
                print(f"❌ Failed to notify customer {customer_user_id}: {notify_error}")
        else:
            print(f"❌ Customer user ID not found in message for order {order_id}")
        
        # Answer the callback to remove loading state
        await callback.answer("✅ Buyurtma qabul qilindi va mijozga xabar yuborildi!", show_alert=True)
        
        print(f"✅ Order {order_id} accepted by {callback.from_user.id}")
        
    except Exception as e:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
        print(f"Error accepting order: {e}")

@router.callback_query(F.data == "cancel_order")
async def cancel_order_callback(callback: CallbackQuery):
    """Handle order cancellation by customer"""
    try:
        user_id = callback.from_user.id
        current_order = db.get_user_current_order(user_id)
        
        if not current_order:
            await callback.answer("❌ Sizda faol buyurtma yo'q!", show_alert=True)
            return
        
        order_id = current_order['id']
        
        # Cancel the order
        db.update_order_status(order_id, "cancelled")
        
        await callback.message.edit_text(
            "❌ <b>Buyurtma bekor qilindi</b>\n\n"
            "Sizning buyurtmangiz bekor qilindi.",
            reply_markup=get_main_menu_keyboard()
        )
        
        await callback.answer("❌ Buyurtma bekor qilindi!", show_alert=True)
        print(f"❌ Order {order_id} cancelled by user {user_id}")
        
    except Exception as e:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
        print(f"Error cancelling order: {e}")

@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order_callback(callback: CallbackQuery):
    """Handle order acceptance by admin"""
    try:
        order_id = callback.data.replace("accept_order_", "")
        
        # Update order status in database
        try:
            db.update_order_status(order_id, "accepted")
            print(f"✅ Order {order_id} status updated to 'accepted' in database")
        except Exception as db_error:
            print(f"❌ Error updating order status in database: {db_error}")
        
        # Extract customer user ID from the message
        message_text = callback.message.text
        customer_user_id = None
        
        # Look for customer user ID in the message
        import re
        user_id_match = re.search(r'🆔 <b>User ID:</b> (\d+)', message_text)
        if user_id_match:
            customer_user_id = int(user_id_match.group(1))
        
        # Edit the message to show it's accepted
        original_text = callback.message.text
        accepted_text = f"{original_text}\n\n✅ <b>QABUL QILINDI</b> #qabul_qilingan\n👨‍💼 <b>Admin:</b> @{callback.from_user.username or callback.from_user.first_name}"
        
        await callback.message.edit_text(
            accepted_text,
        )
        
        # Send acceptance notification to customer if user ID found
        if customer_user_id:
            try:
                # Get order details for notification
                order_details = db.get_order(order_id)
                customer_name = order_details.get('customer_name', 'N/A') if order_details else 'N/A'
                customer_phone = order_details.get('customer_phone', 'N/A') if order_details else 'N/A'
                total_amount = order_details.get('total_amount', 0) if order_details else 0
                delivery_fee = order_details.get('delivery_fee', 0) if order_details else 0
                
                # Get ordered products
                items_text = ""
                if order_details and order_details.get('items'):
                    items = order_details['items']
                    for item in items[:3]:  # Show first 3 items
                        size_text = f" ({item.get('selectedSize', '')})" if item.get('selectedSize') else ""
                        items_text += f"• {item.get('name', 'N/A')}{size_text} x{item.get('quantity', 1)}\n"
                    if len(items) > 3:
                        items_text += f"• ... va yana {len(items) - 3} ta\n"
                
                # Create detailed customer message
                customer_message = f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
                customer_message += f"🆔 <b>Buyurtma raqami:</b> #{order_id}\n"
                customer_message += f"👤 <b>Ism:</b> {customer_name}\n"
                customer_message += f"📞 <b>Telefon:</b> {customer_phone}\n\n"
                
                if items_text:
                    customer_message += f"🍽️ <b>Buyurtma:</b>\n{items_text}"
                
                if delivery_fee > 0:
                    customer_message += f"💰 <b>Taomlar:</b> {total_amount:,} so'm\n"
                    customer_message += f"🚚 <b>Yetkazib berish:</b> {delivery_fee:,} so'm\n"
                    customer_message += f"💳 <b>JAMI:</b> {total_amount + delivery_fee:,} so'm"
                else:
                    customer_message += f"💰 <b>Jami:</b> {total_amount:,} so'm"
                
                customer_message += f"\n\n⏰ <b>Buyurtma qabul qilindi!</b>\n"
                customer_message += f"📦 Tez orada tayyorlanadi va yetkazib beriladi.\n"
                customer_message += f"📞 Savollar uchun: @popays_support"
                await callback.bot.send_message(
                    chat_id=customer_user_id,
                    text=customer_message,
                )
                print(f"✅ Customer acceptance notification sent to user {customer_user_id} for order {order_id}")
            except Exception as notify_error:
                print(f"❌ Failed to notify customer {customer_user_id}: {notify_error}")
        else:
            print(f"❌ Customer user ID not found in message for order {order_id}")
        
        # Answer the callback to remove loading state
        await callback.answer("✅ Buyurtma qabul qilindi va mijozga xabar yuborildi!", show_alert=True)
        
        print(f"✅ Order {order_id} accepted by {callback.from_user.id}")
        
    except Exception as e:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
        print(f"Error accepting order: {e}")

@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order_callback(callback: CallbackQuery):
    """Handle order rejection by admin"""
    try:
        order_id = callback.data.replace("reject_order_", "")
        
        # Update order status in database
        try:
            db.update_order_status(order_id, "rejected")
            print(f"✅ Order {order_id} status updated to 'rejected' in database")
        except Exception as db_error:
            print(f"❌ Error updating order status in database: {db_error}")
        
        # Extract customer user ID from the message
        message_text = callback.message.text
        customer_user_id = None
        
        # Look for customer user ID in the message
        import re
        user_id_match = re.search(r'🆔 <b>User ID:</b> (\d+)', message_text)
        if user_id_match:
            customer_user_id = int(user_id_match.group(1))
        
        # Edit the message to show it's rejected
        original_text = callback.message.text
        rejected_text = f"{original_text}\n\n❌ <b>RAD ETILDI</b>\n👨‍💼 <b>Admin:</b> @{callback.from_user.username or callback.from_user.first_name}"
        
        await callback.message.edit_text(
            rejected_text,
        )
        
        # Send rejection notification to customer if user ID found
        if customer_user_id:
            try:
                # Get order details for rejection message
                order_details = db.get_order(order_id)
                customer_name = order_details.get('customer_name', 'N/A') if order_details else 'N/A'
                
                customer_message = f"😔 <b>Buyurtmangiz rad etildi</b>\n\n"
                customer_message += f"🆔 <b>Buyurtma raqami:</b> #{order_id}\n"
                customer_message += f"👤 <b>Ism:</b> {customer_name}\n\n"
                customer_message += f"❌ <b>Sabab:</b> Buyurtma qabul qilinmadi.\n\n"
                customer_message += f"📞 <b>Batafsil ma'lumot uchun:</b> @popays_support\n"
                customer_message += f"🔄 <b>Yangi buyurtma:</b> /start"
                await callback.bot.send_message(
                    chat_id=customer_user_id,
                    text=customer_message,
                )
                print(f"✅ Customer rejection notification sent to user {customer_user_id} for order {order_id}")
            except Exception as notify_error:
                print(f"❌ Failed to notify customer {customer_user_id}: {notify_error}")
        else:
            print(f"❌ Customer user ID not found in message for order {order_id}")
        
        # Answer the callback to remove loading state
        await callback.answer("❌ Buyurtma rad etildi va mijozga xabar yuborildi!", show_alert=True)
        
        print(f"❌ Order {order_id} rejected by {callback.from_user.id}")
        
    except Exception as e:
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
        print(f"Error rejecting order: {e}")

@router.message(F.location)
async def handle_location(message: Message):
    """Handle location sharing for delivery fee calculation"""
    try:
        # Get user's location
        latitude = message.location.latitude
        longitude = message.location.longitude
        
        # Get user's current order from database
        user_id = message.from_user.id
        current_order = db.get_user_current_order(user_id)
        
        if not current_order:
            await message.reply(
                "❌ Sizda faol buyurtma yo'q!\n\n"
                "Avval buyurtma berish uchun bot menyusidan taom tanlang.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Calculate delivery fee
        order_amount = current_order.get('total_amount', 0)
        delivery_info = calculate_delivery_fee(latitude, longitude, order_amount)
        
        # Format delivery information
        delivery_text = format_delivery_info(delivery_info)
        
        # Update order with location and delivery fee
        db.update_order_location_and_fee(
            order_id=current_order['id'],
            latitude=latitude,
            longitude=longitude,
            delivery_fee=delivery_info['total_delivery_fee'],
            nearest_branch=delivery_info['nearest_branch']
        )
        
        # Send delivery information
        if delivery_info['is_free_delivery']:
            response_text = "✅ <b>Yetkazib berish bepul!</b>"
        else:
            response_text = f"💳 <b>Jami: {order_amount + delivery_info['total_delivery_fee']:,} so'm</b>"
        
        await message.reply(
            response_text,
            reply_markup=get_order_approval_keyboard(),
            parse_mode="HTML"
        )
        
        print(f"📍 Location received from user {user_id}: {latitude}, {longitude}")
        print(f"💰 Delivery fee calculated: {delivery_info['total_delivery_fee']} sum")
        
    except Exception as e:
        await message.reply(
            "❌ Lokatsiyani qayta ishlashda xatolik yuz berdi!\n\n"
            "Iltimos, qaytadan urinib ko'ring.",
            reply_markup=get_main_menu_keyboard()
        )
        print(f"Error handling location: {e}")

@router.message(F.text == "📍 Manzil yuborish")
async def request_location(message: Message):
    """Request location from user"""
    user_id = message.from_user.id
    current_order = db.get_user_current_order(user_id)
    
    if not current_order:
        await message.reply(
            "❌ Sizda faol buyurtma yo'q!\n\n"
            "Avval buyurtma berish uchun bot menyusidan taom tanlang.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await message.reply(
        "📍 <b>Manzilingizni yuboring</b>\n\n"
        "Yetkazib berish uchun sizning joylashuvingizni bilishimiz kerak.\n\n"
        "Telegram'da lokatsiya tugmasini bosing va joylashuvingizni yuboring.",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("admin_page_"))
async def admin_pagination_callback(callback: CallbackQuery):
    """Handle admin panel pagination"""
    try:
        page = int(callback.data.replace("admin_page_", ""))
        await show_admin_panel(callback.message, page)
        await callback.answer()
    except Exception as e:
        print(f"Error in admin pagination: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@router.callback_query(F.data == "admin_main_menu")
async def admin_main_menu_callback(callback: CallbackQuery):
    """Handle return to main menu from admin panel"""
    try:
        await cmd_start(callback.message)
        await callback.answer()
    except Exception as e:
        print(f"Error returning to main menu: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)
