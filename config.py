import os
from dotenv import load_dotenv

# Load environment variables from env.txt
load_dotenv('env.txt')

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8093935798:AAFRrT9aUVIVILO-BwjK_9ZU-lJfHHFQ7ak')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7231910736'))  # Admin Telegram ID
ORDER_CHANNEL_ID = int(os.getenv('ORDER_CHANNEL_ID', '-1002958129439'))  # Buyurtmalar kanali - POPAYS Orders (Kosmonavt)
DEREZLIK_CHANNEL_ID = int(os.getenv('DEREZLIK_CHANNEL_ID', '-1003084723234'))  # Derezlik filiali kanali
ADDITIONAL_CHANNEL_ID = int(os.getenv('ADDITIONAL_CHANNEL_ID', '-1003093515152'))  # Qo'shimcha kanal

# Bot settings
BOT_NAME = "🍕 POPAYS Fast Food"
BOT_DESCRIPTION = "Qo'qondagi eng yaxshi FastFood - tez va mazali taomlar! 🚀"

# Restaurant information
RESTAURANT_NAME = "POPAYS Fast Food"
RESTAURANT_ADDRESS = "Qo'qon Shaxri"
RESTOURAND_FILIAL2 = "Derezlik ko'chasi"
RESTOURAND_FILIAL1 = "Kosmonavt"

RESTAURANT_PHONE1 = "+998 91 269 00 02"
RESTAURANT_PHONE2 = "+998 33 200 22 11"
RESTAURANT_WORKING_HOURS = "8:00 dan 3:00 gacha"

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

# Restaurant branch coordinates (latitude, longitude)
RESTAURANT_BRANCHES = {
    "kosmonavt": {
        "name": "Kosmonavt filiali",
        "address": "Kosmonavt",
        "coordinates": (40.522999, 70.956422)  # latitude, longitude
    },
    "derezlik": {
        "name": "Derezlik filiali", 
        "address": "Derezlik ko'chasi",
        "coordinates": (40.535181, 70.956138)  # latitude, longitude
    }
}

# Delivery settings
MIN_ORDER_AMOUNT = 50000  # in sum
DELIVERY_FEE = 10000  # in sum
FREE_DELIVERY_THRESHOLD = 150000  # in sum
FREE_DELIVERY_RADIUS = 3.0  # km - masofaga qarab to'lovsiz yetkazib berish
DISTANCE_FEE_PER_KM = 5000  # sum per km for distance over 3km
MAX_DELIVERY_DISTANCE = 20.0  # km - maksimal yetkazib berish masofasi
