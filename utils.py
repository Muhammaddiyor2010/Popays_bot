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
    Calculate delivery fee based on distance and order amount
    Returns dict with fee details
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
    
    # Base delivery fee
    base_fee = 0
    
    # Check if order amount qualifies for free delivery
    from config import FREE_DELIVERY_THRESHOLD
    if order_amount >= FREE_DELIVERY_THRESHOLD:
        # Free delivery for large orders regardless of distance
        distance_fee = 0
        total_fee = 0
        is_free = True
    else:
        # Check distance-based fee
        if distance > FREE_DELIVERY_RADIUS:
            # Calculate additional fee for distance over 3km
            extra_distance = distance - FREE_DELIVERY_RADIUS
            distance_fee = math.ceil(extra_distance) * DISTANCE_FEE_PER_KM  # Round up to full km
            is_free = False
        else:
            # Within free delivery radius
            distance_fee = 0
            is_free = False
        
        # Base delivery fee
        from config import DELIVERY_FEE
        total_fee = DELIVERY_FEE + distance_fee
    
    return {
        'nearest_branch': nearest_branch['name'],
        'nearest_branch_address': nearest_branch['address'],
        'distance_km': round(distance, 2),
        'base_delivery_fee': DELIVERY_FEE,
        'distance_fee': distance_fee,
        'total_delivery_fee': total_fee,
        'is_free_delivery': is_free,
        'is_delivery_available': True,
        'free_delivery_threshold': FREE_DELIVERY_THRESHOLD
    }

def format_delivery_info(delivery_info: Dict[str, Any]) -> str:
    """
    Format delivery information for display
    """
    info = f"📍 <b>Eng yaqin filial:</b> {delivery_info['nearest_branch']}\n"
    info += f"🏪 <b>Manzil:</b> {delivery_info['nearest_branch_address']}\n"
    info += f"📏 <b>Masofa:</b> {delivery_info['distance_km']} km\n\n"
    
    if delivery_info['is_free_delivery']:
        info += "🆓 <b>Yetkazib berish bepul!</b>\n"
        info += f"(Buyurtma miqdori {delivery_info['free_delivery_threshold']:,} so'm dan ortiq)"
    else:
        info += "💰 <b>Yetkazib berish to'lovi:</b>\n"
        
        if delivery_info['distance_fee'] > 0:
            info += f"• Asosiy to'lov: {delivery_info['base_delivery_fee']:,} so'm\n"
            info += f"• Masofa to'lovi ({delivery_info['distance_km']} km): {delivery_info['distance_fee']:,} so'm\n"
            info += f"• <b>Jami: {delivery_info['total_delivery_fee']:,} so'm</b>"
        else:
            info += f"• {delivery_info['total_delivery_fee']:,} so'm"
    
    return info

