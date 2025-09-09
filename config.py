import os
from dotenv import load_dotenv

# Load environment variables from env.txt
load_dotenv('env.txt')

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093935798:AAGuZH0IT0GM2zvm1K57c4YvW5SjDlg3J7o')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7231910736'))  # Admin Telegram ID
ORDER_CHANNEL_ID = int(os.getenv('ORDER_CHANNEL_ID', '-1002958129439'))  # Buyurtmalar kanali - POPAYS Orders

# Bot settings
BOT_NAME = "🍕 POPAYS Fast Food"
BOT_DESCRIPTION = "Qo'qondagi eng yaxshi FastFood - tez va mazali taomlar! 🚀"

# Restaurant information
RESTAURANT_NAME = "POPAYS Fast Food"
RESTAURANT_ADDRESS = "Qo'qon Shaxri, Derezlik ko'chasi"
RESTAURANT_PHONE = "+998 91 269 00 02"
RESTAURANT_WORKING_HOURS = "24/7 - kun bo'yi"

# Restaurant features
RESTAURANT_FEATURES = [
    "🍔 Eng mazali va sifatli burgerlar",
    "🌯 An'anaviy va zamonaviy lavashlar",
    "🍕 Italiya uslubidagi pizzalar",
    "🥤 Sovuq va issiq ichimliklar",
    "🌭 Klassik va maxsus hot doglar",
    "🍽️ Maxsus kombinatsiyalar"
]

# Web App URL
WEBAPP_URL = "https://my-popays.vercel.app/"

# Delivery settings
MIN_ORDER_AMOUNT = 50000  # in sum
DELIVERY_FEE = 10000  # in sum
FREE_DELIVERY_THRESHOLD = 150000  # in sum
