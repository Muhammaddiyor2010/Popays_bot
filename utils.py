import math
from typing import Tuple, Dict, Any
from config import RESTAURANT_BRANCHES, FREE_DELIVERY_RADIUS, DISTANCE_FEE_PER_KM, MAX_DELIVERY_DISTANCE

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula
    Returns distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance

def find_nearest_branch(customer_lat: float, customer_lon: float) -> Tuple[str, float]:
    """
    Find the nearest restaurant branch to customer location
    Returns (branch_name, distance_km)
    """
    min_distance = float('inf')
    nearest_branch = None
    
    for branch_key, branch_info in RESTAURANT_BRANCHES.items():
        branch_lat, branch_lon = branch_info['coordinates']
        distance = calculate_distance(customer_lat, customer_lon, branch_lat, branch_lon)
        
        if distance < min_distance:
            min_distance = distance
            nearest_branch = branch_key
    
    return nearest_branch, min_distance

def calculate_delivery_fee(customer_lat: float, customer_lon: float, order_amount: int) -> Dict[str, Any]:
    """
    Show delivery reminder instead of calculating actual fee
    Returns dict with reminder details
    """
    # Find nearest branch
    nearest_branch_key, distance = find_nearest_branch(customer_lat, customer_lon)
    nearest_branch = RESTAURANT_BRANCHES[nearest_branch_key]
    
    # Check if distance exceeds maximum delivery distance
    if distance > MAX_DELIVERY_DISTANCE:
        return {
            'nearest_branch': nearest_branch['name'],
            'nearest_branch_address': nearest_branch['address'],
            'distance_km': round(distance, 2),
            'is_delivery_available': False,
            'max_delivery_distance': MAX_DELIVERY_DISTANCE,
            'error_message': f"❌ Kechirasiz, sizning joylashuvingiz {distance:.1f} km uzoqlikda.\n\nSizga yetkazib bera olmaymiz. Maksimal yetkazib berish masofasi {MAX_DELIVERY_DISTANCE} km."
        }
    
    # Show reminder instead of calculating actual fee
    if distance > FREE_DELIVERY_RADIUS:
        # Distance is more than 3km - show reminder about possible delivery fee
        reminder_message = f"ℹ️ <b>Eslatma:</b> Sizning joylashuvingiz {distance:.1f} km uzoqlikda.\n\nAgar 3km dan uzoq bo'lsa, yetkazib berish uchun pul olinishi mumkin."
        is_free = False
    else:
        # Within 3km - free delivery
        reminder_message = f"✅ <b>Yetkazib berish bepul!</b>\n\nSizning joylashuvingiz {distance:.1f} km uzoqlikda (3km dan kam)."
        is_free = True
    
    return {
        'nearest_branch': nearest_branch['name'],
        'nearest_branch_address': nearest_branch['address'],
        'distance_km': round(distance, 2),
        'total_delivery_fee': 0,  # No actual fee calculation
        'is_free_delivery': is_free,
        'is_delivery_available': True,
        'reminder_message': reminder_message
    }

def format_delivery_info(delivery_info: Dict[str, Any]) -> str:
    """
    Format delivery information for display with reminder message
    """
    info = f"📍 <b>Eng yaqin filial:</b> {delivery_info['nearest_branch']}\n"
    info += f"🏪 <b>Manzil:</b> {delivery_info['nearest_branch_address']}\n"
    info += f"📏 <b>Masofa:</b> {delivery_info['distance_km']} km\n\n"
    
    # Use the reminder message instead of fee calculation
    if 'reminder_message' in delivery_info:
        info += delivery_info['reminder_message']
    else:
        # Fallback for backward compatibility
        if delivery_info['is_free_delivery']:
            info += "🆓 <b>Yetkazib berish bepul!</b>"
        else:
            info += "ℹ️ <b>Eslatma:</b> Yetkazib berish uchun pul olinishi mumkin."
    
    return info

