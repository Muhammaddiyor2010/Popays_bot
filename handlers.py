from aiogram import Router, F
from aiogram.types import Message, WebAppInfo, WebAppData, CallbackQuery
from aiogram.filters import Command
import uuid
import json

from config import BOT_NAME, BOT_DESCRIPTION, RESTAURANT_NAME, RESTAURANT_ADDRESS, RESTAURANT_PHONE, RESTAURANT_WORKING_HOURS, RESTAURANT_FEATURES, ORDER_CHANNEL_ID, ADMIN_ID
from keyboards import get_start_keyboard, get_main_menu_keyboard, get_back_keyboard, get_order_approval_keyboard
from database import db

# Create router
router = Router()

# Admin password
ADMIN_PASSWORD = "202420"

# Track users waiting for admin password
waiting_for_admin_password = set()

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
📍 <i>{RESTAURANT_ADDRESS}</i>
📞 <i>{RESTAURANT_PHONE}</i>
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
        await message.answer(
            "❌ Siz admin emassiz! Bu buyruq faqat admin uchun.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Ask for password
    waiting_for_admin_password.add(user_id)
    await message.answer(
        "🔐 <b>Admin panelga kirish</b>\n\n"
        "Parolni kiriting:",
        reply_markup=get_back_keyboard()
    )

async def show_admin_panel(message: Message):
    """Show admin panel after password verification"""
    try:
        # Get statistics
        stats = db.get_statistics()
        
        # Get recent orders
        recent_orders = db.get_recent_orders_admin(limit=10)
        
        # Get users with orders
        users_with_orders = db.get_all_users_with_orders(limit=20)
        
        # Format admin panel message
        admin_message = f"""
🔧 <b>ADMIN PANEL</b> 🔧

📊 <b>Umumiy statistika:</b>
• Jami buyurtmalar: {stats.get('total_orders', 0)} ta
• Jami daromad: {stats.get('total_revenue', 0):,.0f} so'm
• Jami lokatsiyalar: {stats.get('total_locations', 0)} ta

📈 <b>Buyurtmalar holati bo'yicha:</b>
"""
        
        # Add order status breakdown
        orders_by_status = stats.get('orders_by_status', {})
        status_emojis = {
            'pending': '⏳',
            'accepted': '✅', 
            'rejected': '❌',
            'completed': '🎉',
            'cancelled': '🚫'
        }
        
        status_texts = {
            'pending': 'Kutilmoqda',
            'accepted': 'Qabul qilingan',
            'rejected': 'Rad etilgan', 
            'completed': 'Tugallangan',
            'cancelled': 'Bekor qilingan'
        }
        
        for status, count in orders_by_status.items():
            emoji = status_emojis.get(status, '❓')
            text = status_texts.get(status, status)
            admin_message += f"• {emoji} {text}: {count} ta\n"
        
        admin_message += f"\n👥 <b>Foydalanuvchilar ({len(users_with_orders)} ta):</b>\n"
        
        # Add users list
        for i, user in enumerate(users_with_orders[:10], 1):
            username = user['username'] if user['username'] != 'N/A' else 'N/A'
            first_name = user['first_name'] if user['first_name'] != 'N/A' else 'N/A'
            admin_message += f"""
<b>{i}. @{username}</b> ({first_name})
🆔 ID: {user['user_id']}
📦 Buyurtmalar: {user['order_count']} ta
💰 Jami sarflangan: {user['total_spent']:,.0f} so'm
📅 Oxirgi buyurtma: {user['last_order_date'][:16]}
"""
        
        if len(users_with_orders) > 10:
            admin_message += f"\n... va yana {len(users_with_orders) - 10} ta foydalanuvchi"
        
        admin_message += f"\n\n📋 <b>So'nggi buyurtmalar ({len(recent_orders)} ta):</b>\n"
        
        # Add recent orders
        for i, order in enumerate(recent_orders[:5], 1):
            status_emoji = status_emojis.get(order['status'], '❓')
            customer_name = order['customer_name'] if order['customer_name'] != 'N/A' else 'N/A'
            username = order['username'] if order['username'] != 'N/A' else 'N/A'
            admin_message += f"""
<b>{i}. Buyurtma #{order['id']}</b> {status_emoji}
👤 Mijoz: {customer_name} (@{username})
💰 Summa: {order['total_amount']:,.0f} so'm
📅 Sana: {order['created_at'][:16]}
"""
        
        if len(recent_orders) > 5:
            admin_message += f"\n... va yana {len(recent_orders) - 5} ta buyurtma"
        
        await message.answer(admin_message, reply_markup=get_main_menu_keyboard())
        
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
        
        # Parse JSON data
        import json
        order_data = json.loads(data)
        
        print(f"📥 Received web app data: {data}")
        print(f"📥 Parsed order data: {order_data}")
        
        # Check if this is location_complete, mapData or order data
        if order_data.get('type') == 'location_complete':
            # This is location_complete structure
            coordinates = order_data.get('coordinates', {})
            address = order_data.get('address', 'N/A')
            maps = order_data.get('maps', {})
            
            print(f"📍 Location complete data received: {order_data}")
            
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
                await message.answer(error_message, reply_markup=get_main_menu_keyboard())
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
                await message.answer(error_message, reply_markup=get_main_menu_keyboard())
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
            
            # Send location data to channel
            try:
                await message.bot.send_message(
                    ORDER_CHANNEL_ID, 
                    location_message, 
                    reply_markup=get_order_approval_keyboard(location_id)
                )
                print(f"✅ Lokatsiya ma'lumotlari kanalga yuborildi: {ORDER_CHANNEL_ID} - Location ID: {location_id}")
                
                # Send location as Telegram location
                if coordinates.get('latitude') and coordinates.get('longitude'):
                    try:
                        await message.bot.send_location(
                            chat_id=ORDER_CHANNEL_ID,
                            latitude=coordinates.get('latitude'),
                            longitude=coordinates.get('longitude')
                        )
                        print(f"✅ Lokatsiya kanalga yuborildi: {coordinates.get('latitude')}, {coordinates.get('longitude')}")
                    except Exception as loc_error:
                        print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                
            # Send confirmation to user
            await message.answer(
                "🗺️ <b>Lokatsiya ma'lumotlari qabul qilindi va kanalga yuborildi!</b>",
                reply_markup=get_main_menu_keyboard()
            )
            
        elif order_data.get('mapData') and not order_data.get('type'):
            # This is mapData structure
            map_data = order_data.get('mapData', {})
            customer = map_data.get('customer', {})
            
            print(f"📍 Map data received: {map_data}")
            
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
            
            # Send map data to channel
            try:
                await message.bot.send_message(
                    ORDER_CHANNEL_ID, 
                    map_message, 
                    reply_markup=get_order_approval_keyboard(map_id)
                )
                print(f"✅ Xarita ma'lumotlari kanalga yuborildi: {ORDER_CHANNEL_ID} - Map ID: {map_id}")
                
                # Send location as Telegram location
                coords = map_data.get('coordinates', {})
                if coords.get('latitude') and coords.get('longitude'):
                    try:
                        await message.bot.send_location(
                            chat_id=ORDER_CHANNEL_ID,
                            latitude=coords.get('latitude'),
                            longitude=coords.get('longitude')
                        )
                        print(f"✅ Lokatsiya kanalga yuborildi: {coords.get('latitude')}, {coords.get('longitude')}")
                    except Exception as loc_error:
                        print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                
            # Send confirmation to user
            await message.answer(
                "🗺️ <b>Xarita ma'lumotlari qabul qilindi va kanalga yuborildi!</b>",
                reply_markup=get_main_menu_keyboard()
            )
            
        elif order_data.get('type') == 'order':
            # This is order data
            customer = order_data.get('customer', {})
            items = order_data.get('items', [])
            total = order_data.get('total', 0)
            timestamp = order_data.get('timestamp', '')
            restaurant = order_data.get('restaurant', 'POPAYS')
            map_data = order_data.get('mapData', {})
            
            # Save order to database
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
                order_id = str(uuid.uuid4())[:8]  # Fallback ID
            
            # Format order message
            order_message = f"""
🆕 <b>YANGI BUYURTMA!</b> 🆕

🏪 <b>Filial:</b> {order_data.get('branch', 'N/A')}

👤 <b>Mijoz ma'lumotlari:</b>
• Ism: {customer.get('name', 'N/A')}
• Telefon: {customer.get('phone', 'N/A')}
• Manzil: {customer.get('location', 'N/A')}
"""
            
            # Add map data if available
            if map_data and map_data.get('coordinates'):
                coords = map_data['coordinates']
                map_links = map_data.get('mapLinks', {})
                
                print(f"📍 Map data found: {map_data}")
                print(f"📍 Coordinates: {coords}")
                
                order_message += f"""
📍 <b>Lokatsiya ma'lumotlari:</b>
• Koordinatalar: {coords.get('latitude', 'N/A')}, {coords.get('longitude', 'N/A')}
• Aniqlik: {coords.get('accuracy', 'N/A')}m
"""
                
                # Add map links
                if map_links:
                    order_message += "\n🗺️ <b>Xarita linklari:</b>\n"
                    if map_links.get('google'):
                        order_message += f"• Google Maps: {map_links['google']}\n"
                    if map_links.get('yandex'):
                        order_message += f"• Yandex Maps: {map_links['yandex']}\n"
                    if map_links.get('osm'):
                        order_message += f"• OpenStreetMap: {map_links['osm']}\n"
            else:
                print(f"📍 No map data found in order: {order_data}")
            
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
                order_message += f"\n💰 <b>Jami: {total:,} so'm</b>"
            
            order_message += f"""
🏪 <b>Restoran:</b> {restaurant}
🏢 <b>Filial:</b> {order_data.get('branch', 'N/A')}
⏰ <b>Vaqt:</b> {timestamp}
📱 <b>Telegram:</b> @{message.from_user.username or 'N/A'}
🆔 <b>User ID:</b> {message.from_user.id}
🆔 <b>Order ID:</b> {order_id}
👤 <b>Customer User ID:</b> {message.from_user.id}
"""
            
            # Send order to admin
            await message.answer(
                "✅ <b>Buyurtma qabul qilindi!</b> Tez orada operatorlarimiz siz bilan bog'lanishadi.",
                reply_markup=get_main_menu_keyboard()
            )
            
            # Send detailed order to channel with inline keyboard
            try:
                await message.bot.send_message(
                    ORDER_CHANNEL_ID, 
                    order_message, 
                    reply_markup=get_order_approval_keyboard(order_id)
                )
                print(f"✅ Buyurtma kanalga yuborildi: {ORDER_CHANNEL_ID} (POPAYS Orders) - Order ID: {order_id}")
                
                # If map data available, also send location
                print(f"🔍 DEBUG: map_data exists: {bool(map_data)}")
                if map_data:
                    print(f"🔍 DEBUG: map_data content: {map_data}")
                    coords = map_data.get('coordinates', {})
                    print(f"🔍 DEBUG: coordinates exists: {bool(coords)}")
                    if coords:
                        print(f"🔍 DEBUG: coordinates content: {coords}")
                        lat = coords.get('latitude')
                        lon = coords.get('longitude')
                        print(f"🔍 DEBUG: latitude: {lat} (type: {type(lat)})")
                        print(f"🔍 DEBUG: longitude: {lon} (type: {type(lon)})")
                        
                        if lat and lon:
                            print(f"📍 Attempting to send location to channel: {coords}")
                            try:
                                # Send location as Telegram location
                                await message.bot.send_location(
                                    chat_id=ORDER_CHANNEL_ID,
                                    latitude=float(lat),
                                    longitude=float(lon)
                                )
                                print(f"✅ Lokatsiya kanalga yuborildi: {lat}, {lon}")
                            except Exception as loc_error:
                                print(f"❌ Lokatsiya yuborishda xatolik: {loc_error}")
                                print(f"❌ Error details: {type(loc_error).__name__}: {str(loc_error)}")
                        else:
                            print(f"❌ Invalid coordinates: lat={lat}, lon={lon}")
                    else:
                        print(f"❌ No coordinates in map_data")
                else:
                    print(f"❌ No map_data found")
                
            except Exception as e:
                print(f"❌ Kanalga yuborishda xatolik: {e}")
                # If channel not accessible, send to admin
                try:
                    from config import ADMIN_ID
                    # Add order info to admin message too
                    admin_order_message = order_message + f"\n🆔 **Order ID: {order_id}**\n👤 **Customer User ID: {message.from_user.id}**"
                    await message.bot.send_message(
                        ADMIN_ID, 
                        admin_order_message, 
                        reply_markup=get_order_approval_keyboard(order_id)
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
                    # If admin ID not set, send to the user who sent the order
                    await message.answer(f"📋 Buyurtma ma'lumotlari:\n{order_message}")
                
        else:
            await message.answer("❌ <b>Noto'g'ri buyurtma formati!</b>")
            
    except json.JSONDecodeError:
        await message.answer("❌ <b>Buyurtma ma'lumotlari noto'g'ri formatda!</b>")
    except Exception as e:
        await message.answer(f"❌ <b>Xatolik yuz berdi:</b> {str(e)}")
        print(f"Web app handler error: {e}")



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
        orders_text = f"📋 <b>Sizning buyurtmalaringiz</b> ({len(orders)} ta)\n\n"
        
        for i, order in enumerate(orders, 1):
            status_emoji = {
                'pending': '⏳',
                'accepted': '✅',
                'rejected': '❌',
                'completed': '🎉',
                'cancelled': '🚫'
            }.get(order['status'], '❓')
            
            status_text = {
                'pending': 'Kutilmoqda',
                'accepted': 'Qabul qilingan',
                'rejected': 'Rad etilgan',
                'completed': 'Tugallangan',
                'cancelled': 'Bekor qilingan'
            }.get(order['status'], order['status'])
            
            orders_text += f"<b>{i}. Buyurtma #{order['id']}</b>\n"
            orders_text += f"{status_emoji} <b>Holat:</b> {status_text}\n"
            orders_text += f"💰 <b>Summa:</b> {order['total_amount']:,.0f} so'm\n"
            orders_text += f"📅 <b>Sana:</b> {order['created_at'][:16]}\n"
            
            # Add items if available
            if order.get('items'):
                orders_text += "🍽️ <b>Taomlar:</b>\n"
                for item in order['items'][:3]:  # Show first 3 items
                    size_text = f" ({item['selectedSize']})" if item.get('selectedSize') else ""
                    orders_text += f"• {item['name']}{size_text} x{item['quantity']}\n"
                if len(order['items']) > 3:
                    orders_text += f"• ... va yana {len(order['items']) - 3} ta\n"
            
            orders_text += "\n" + "─" * 30 + "\n\n"
        
        # Add summary
        total_spent = sum(order['total_amount'] for order in orders)
        orders_text += f"📊 <b>Jami:</b> {len(orders)} ta buyurtma\n"
        orders_text += f"💰 <b>Jami sarflangan:</b> {total_spent:,.0f} so'm"
        
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
📍 <i>{RESTAURANT_ADDRESS}</i>
📞 <i>{RESTAURANT_PHONE}</i>
🕐 <i>{RESTAURANT_WORKING_HOURS}</i>

🍽️ <b>Bizning taomlarimiz:</b>
• Taze va sifatli ingredientlar
• Tez va qulay yetkazib berish
• Professional oshpazlar
• 24/7 mijozlar xizmati

🎉 <b>Maxsus imkoniyatlar:</b>
• 20% chegirma 100,000 so'mdan ortiq buyurtmaga
• Bepul yetkazib berish 50,000 so'mdan ortiq buyurtmaga
• Har 3-buyurtmaga bepul desert
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
    """Handle password input for admin panel"""
    user_id = message.from_user.id
    
    # Check if user is waiting for admin password
    if user_id in waiting_for_admin_password:
        # Remove from waiting list
        waiting_for_admin_password.remove(user_id)
        
        # Check password
        if message.text == ADMIN_PASSWORD:
            await message.answer("✅ <b>Parol to'g'ri! Admin panelga kirdingiz.</b>")
            await show_admin_panel(message)
        else:
            await message.answer(
                "❌ <b>Noto'g'ri parol!</b> Iltimos, qayta urinib ko'ring.\n\n"
                "Admin panelga kirish uchun /admin buyrug'ini qayta yuboring.",
                reply_markup=get_main_menu_keyboard()
            )
        return
    
    # If not waiting for password, handle as regular message
    await echo_handler(message)

async def echo_handler(message: Message):
    """Handle all other messages"""
    await message.answer(
        "❓ <b>Tushunarsiz buyruq.</b> Bosh sahifaga qaytish uchun /start ni bosing.",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data.startswith("accept_order_"))
async def accept_order_callback(callback: CallbackQuery):
    """Handle order acceptance"""
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
        user_id_match = re.search(r'👤 \*\*Customer User ID: (\d+)\*\*', message_text)
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
                customer_message = f"""
🎉 <b>BUYURTMANGIZ QABUL QILINDI!</b> 🎉

✅ Sizning buyurtmangiz muvaffaqiyatli qabul qilindi!

👨‍💼 <b>Admin:</b> @{callback.from_user.username or callback.from_user.first_name}
🆔 <b>Buyurtma ID:</b> {order_id}
⏰ <b>Qabul qilingan vaqt:</b> {callback.message.date.strftime('%d.%m.%Y %H:%M')}

🚚 <b>Keyingi qadamlar:</b>
• Operatorlarimiz tez orada siz bilan bog'lanishadi
• Yetkazib berish vaqti haqida ma'lumot beriladi
• To'lov usuli tasdiqlanadi

📞 <b>Savollar bo'lsa:</b> @popays_support

🍕 <b>POPAYS Fast Food</b> - Qo'qondagi eng yaxshi taomlar!
"""
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

@router.callback_query(F.data.startswith("reject_order_"))
async def reject_order_callback(callback: CallbackQuery):
    """Handle order rejection"""
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
        user_id_match = re.search(r'👤 \*\*Customer User ID: (\d+)\*\*', message_text)
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
                customer_message = f"""
😔 <b>BUYURTMANGIZ RAD ETILDI</b>

❌ Afsuski, sizning buyurtmangiz qabul qilinmadi.

👨‍💼 <b>Admin:</b> @{callback.from_user.username or callback.from_user.first_name}
🆔 <b>Buyurtma ID:</b> {order_id}
⏰ <b>Rad etilgan vaqt:</b> {callback.message.date.strftime('%d.%m.%Y %H:%M')}

📞 <b>Sababni bilish uchun:</b> @popays_support
🔄 <b>Yangi buyurtma berish:</b> /start

🍕 <b>POPAYS Fast Food</b> - Qo'qondagi eng yaxshi taomlar!
"""
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
