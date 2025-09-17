import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "delivery_bot.db"):
        """Initialize database manager with SQLite database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create orders table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        customer_name TEXT,
                        customer_phone TEXT,
                        customer_location TEXT,
                        order_data TEXT NOT NULL,
                        total_amount REAL,
                        latitude REAL,
                        longitude REAL,
                        delivery_fee INTEGER DEFAULT 0,
                        nearest_branch TEXT,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create locations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS locations (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        address TEXT,
                        latitude REAL,
                        longitude REAL,
                        accuracy REAL,
                        map_links TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create order_items table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        selected_size TEXT,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    )
                ''')
                
                # Create admin_logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admin_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        action TEXT NOT NULL,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Migrate existing database if needed
                self._migrate_database(cursor)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
                # Add new columns to existing orders table if they don't exist
                self._migrate_orders_table()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def _migrate_orders_table(self):
        """Add new columns to orders table if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if latitude column exists
                cursor.execute("PRAGMA table_info(orders)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Add missing columns
                if 'latitude' not in columns:
                    cursor.execute("ALTER TABLE orders ADD COLUMN latitude REAL")
                    logger.info("Added latitude column to orders table")
                
                if 'longitude' not in columns:
                    cursor.execute("ALTER TABLE orders ADD COLUMN longitude REAL")
                    logger.info("Added longitude column to orders table")
                
                if 'delivery_fee' not in columns:
                    cursor.execute("ALTER TABLE orders ADD COLUMN delivery_fee INTEGER DEFAULT 0")
                    logger.info("Added delivery_fee column to orders table")
                
                if 'nearest_branch' not in columns:
                    cursor.execute("ALTER TABLE orders ADD COLUMN nearest_branch TEXT")
                    logger.info("Added nearest_branch column to orders table")
                
                conn.commit()
                logger.info("Orders table migration completed successfully")
                
        except Exception as e:
            logger.error(f"Error migrating orders table: {e}")
            raise
    
    def _migrate_database(self, cursor):
        """Migrate existing database schema if needed"""
        try:
            # Check if username column exists in orders table
            cursor.execute("PRAGMA table_info(orders)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'username' not in columns:
                logger.info("Migrating orders table - adding username column")
                cursor.execute("ALTER TABLE orders ADD COLUMN username TEXT")
            
            if 'first_name' not in columns:
                logger.info("Migrating orders table - adding first_name column")
                cursor.execute("ALTER TABLE orders ADD COLUMN first_name TEXT")
            
            if 'customer_name' not in columns:
                logger.info("Migrating orders table - adding customer_name column")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT")
            
            if 'customer_phone' not in columns:
                logger.info("Migrating orders table - adding customer_phone column")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_phone TEXT")
            
            if 'customer_location' not in columns:
                logger.info("Migrating orders table - adding customer_location column")
                cursor.execute("ALTER TABLE orders ADD COLUMN customer_location TEXT")
            
            if 'total_amount' not in columns:
                logger.info("Migrating orders table - adding total_amount column")
                cursor.execute("ALTER TABLE orders ADD COLUMN total_amount REAL")
            
            if 'status' not in columns:
                logger.info("Migrating orders table - adding status column")
                cursor.execute("ALTER TABLE orders ADD COLUMN status TEXT DEFAULT 'pending'")
            
            if 'updated_at' not in columns:
                logger.info("Migrating orders table - adding updated_at column")
                cursor.execute("ALTER TABLE orders ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Check if locations table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='locations'")
            if not cursor.fetchone():
                logger.info("Creating locations table")
                cursor.execute('''
                    CREATE TABLE locations (
                        id TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        address TEXT,
                        latitude REAL,
                        longitude REAL,
                        accuracy REAL,
                        map_links TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Check if order_items table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_items'")
            if not cursor.fetchone():
                logger.info("Creating order_items table")
                cursor.execute('''
                    CREATE TABLE order_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        selected_size TEXT,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    )
                ''')
            
            # Check if admin_logs table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_logs'")
            if not cursor.fetchone():
                logger.info("Creating admin_logs table")
                cursor.execute('''
                    CREATE TABLE admin_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        action TEXT NOT NULL,
                        details TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            logger.info("Database migration completed")
            
        except Exception as e:
            logger.error(f"Error during database migration: {e}")
            raise
    
    def create_order(self, user_id: int, username: str, first_name: str, 
                    order_data: Dict[str, Any]) -> str:
        """Create a new order in the database"""
        try:
            order_id = str(uuid.uuid4())[:8]
            
            # Extract customer information
            customer = order_data.get('customer', {})
            customer_name = customer.get('name', '')
            customer_phone = customer.get('phone', '')
            customer_location = customer.get('location', '')
            
            # Calculate total amount
            total_amount = order_data.get('total', 0)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert order
                cursor.execute('''
                    INSERT INTO orders (id, user_id, username, first_name, customer_name, 
                                      customer_phone, customer_location, order_data, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (order_id, user_id, username, first_name, customer_name, 
                     customer_phone, customer_location, json.dumps(order_data), total_amount))
                
                # Insert order items
                items = order_data.get('items', [])
                for item in items:
                    cursor.execute('''
                        INSERT INTO order_items (order_id, item_name, quantity, price, selected_size)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (order_id, item.get('name', ''), item.get('quantity', 1), 
                         item.get('total', 0), item.get('selectedSize', '')))
                
                conn.commit()
                logger.info(f"Order {order_id} created successfully")
                return order_id
                
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    def create_location(self, user_id: int, username: str, first_name: str, 
                       location_data: Dict[str, Any]) -> str:
        """Create a new location record in the database"""
        try:
            location_id = str(uuid.uuid4())[:8]
            
            # Extract location information
            coordinates = location_data.get('coordinates', {})
            address = location_data.get('address', '')
            latitude = coordinates.get('latitude')
            longitude = coordinates.get('longitude')
            accuracy = coordinates.get('accuracy')
            maps = location_data.get('maps', {})
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO locations (id, user_id, username, first_name, address,
                                         latitude, longitude, accuracy, map_links)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (location_id, user_id, username, first_name, address,
                     latitude, longitude, accuracy, json.dumps(maps)))
                
                conn.commit()
                logger.info(f"Location {location_id} created successfully")
                return location_id
                
        except Exception as e:
            logger.error(f"Error creating location: {e}")
            raise
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM orders WHERE id = ?
                ''', (order_id,))
                
                order_row = cursor.fetchone()
                if not order_row:
                    return None
                
                # Get order items
                cursor.execute('''
                    SELECT item_name, quantity, price, selected_size 
                    FROM order_items WHERE order_id = ?
                ''', (order_id,))
                
                items = cursor.fetchall()
                
                # Reconstruct order data
                order_data = {
                    'id': order_row[0],
                    'user_id': order_row[1],
                    'username': order_row[2],
                    'first_name': order_row[3],
                    'customer_name': order_row[4],
                    'customer_phone': order_row[5],
                    'customer_location': order_row[6],
                    'order_data': json.loads(order_row[7]),
                    'total_amount': order_row[8],
                    'latitude': order_row[9],
                    'longitude': order_row[10],
                    'delivery_fee': order_row[11] or 0,
                    'nearest_branch': order_row[12],
                    'status': order_row[13],
                    'created_at': order_row[14],
                    'updated_at': order_row[15],
                    'items': [
                        {
                            'name': item[0],
                            'quantity': item[1],
                            'total': item[2],
                            'selectedSize': item[3]
                        } for item in items
                    ]
                }
                
                return order_data
                
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    def get_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get location by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM locations WHERE id = ?
                ''', (location_id,))
                
                location_row = cursor.fetchone()
                if not location_row:
                    return None
                
                location_data = {
                    'id': location_row[0],
                    'user_id': location_row[1],
                    'username': location_row[2],
                    'first_name': location_row[3],
                    'address': location_row[4],
                    'latitude': location_row[5],
                    'longitude': location_row[6],
                    'accuracy': location_row[7],
                    'map_links': json.loads(location_row[8]) if location_row[8] else {},
                    'created_at': location_row[9]
                }
                
                return location_data
                
        except Exception as e:
            logger.error(f"Error getting location {location_id}: {e}")
            return None
    
    def update_order_status(self, order_id: str, status: str) -> bool:
        """Update order status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status, order_id))
                
                conn.commit()
                logger.info(f"Order {order_id} status updated to {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent orders"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM orders WHERE user_id = ? 
                    ORDER BY created_at DESC LIMIT ?
                ''', (user_id, limit))
                
                orders = cursor.fetchall()
                
                result = []
                for order_row in orders:
                    # Get order items
                    cursor.execute('''
                        SELECT item_name, quantity, price, selected_size 
                        FROM order_items WHERE order_id = ?
                    ''', (order_row[0],))
                    
                    items = cursor.fetchall()
                    
                    order_data = {
                        'id': order_row[0],
                        'user_id': order_row[1],
                        'username': order_row[2],
                        'first_name': order_row[3],
                        'customer_name': order_row[4],
                        'customer_phone': order_row[5],
                        'customer_location': order_row[6],
                        'order_data': json.loads(order_row[7]),
                        'total_amount': order_row[8],
                        'latitude': order_row[9],
                        'longitude': order_row[10],
                        'delivery_fee': order_row[11] or 0,
                        'nearest_branch': order_row[12],
                        'status': order_row[13],
                        'created_at': order_row[14],
                        'updated_at': order_row[15],
                        'items': [
                            {
                                'name': item[0],
                                'quantity': item[1],
                                'total': item[2],
                                'selectedSize': item[3]
                            } for item in items
                        ]
                    }
                    result.append(order_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting user orders: {e}")
            return []
    
    def get_all_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all orders (for admin)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM orders ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
                
                orders = cursor.fetchall()
                
                result = []
                for order_row in orders:
                    # Get order items
                    cursor.execute('''
                        SELECT item_name, quantity, price, selected_size 
                        FROM order_items WHERE order_id = ?
                    ''', (order_row[0],))
                    
                    items = cursor.fetchall()
                    
                    order_data = {
                        'id': order_row[0],
                        'user_id': order_row[1],
                        'username': order_row[2],
                        'first_name': order_row[3],
                        'customer_name': order_row[4],
                        'customer_phone': order_row[5],
                        'customer_location': order_row[6],
                        'order_data': json.loads(order_row[7]),
                        'total_amount': order_row[8],
                        'latitude': order_row[9],
                        'longitude': order_row[10],
                        'delivery_fee': order_row[11] or 0,
                        'nearest_branch': order_row[12],
                        'status': order_row[13],
                        'created_at': order_row[14],
                        'updated_at': order_row[15],
                        'items': [
                            {
                                'name': item[0],
                                'quantity': item[1],
                                'total': item[2],
                                'selectedSize': item[3]
                            } for item in items
                        ]
                    }
                    result.append(order_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting all orders: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count orders by status
                cursor.execute('''
                    SELECT status, COUNT(*) FROM orders GROUP BY status
                ''')
                status_counts = dict(cursor.fetchall())
                
                # Total orders
                cursor.execute('SELECT COUNT(*) FROM orders')
                total_orders = cursor.fetchone()[0]
                
                # Total revenue
                cursor.execute('SELECT SUM(total_amount) FROM orders WHERE status = "completed"')
                total_revenue = cursor.fetchone()[0] or 0
                
                # Total locations
                cursor.execute('SELECT COUNT(*) FROM locations')
                total_locations = cursor.fetchone()[0]
                
                return {
                    'total_orders': total_orders,
                    'total_revenue': total_revenue,
                    'total_locations': total_locations,
                    'orders_by_status': status_counts
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_all_users_with_orders(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all users who have placed orders (for admin)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT DISTINCT 
                        user_id, 
                        username, 
                        first_name,
                        COUNT(*) as order_count,
                        SUM(total_amount) as total_spent,
                        MAX(created_at) as last_order_date
                    FROM orders 
                    GROUP BY user_id, username, first_name
                    ORDER BY last_order_date DESC
                    LIMIT ?
                ''', (limit,))
                
                users = cursor.fetchall()
                
                result = []
                for user_row in users:
                    user_data = {
                        'user_id': user_row[0],
                        'username': user_row[1] or 'N/A',
                        'first_name': user_row[2] or 'N/A',
                        'order_count': user_row[3],
                        'total_spent': user_row[4] or 0,
                        'last_order_date': user_row[5]
                    }
                    result.append(user_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting users with orders: {e}")
            return []
    
    def get_recent_orders_admin(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent orders for admin panel with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM orders ORDER BY created_at DESC LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                orders = cursor.fetchall()
                
                result = []
                for order_row in orders:
                    # Get order items
                    cursor.execute('''
                        SELECT item_name, quantity, price, selected_size 
                        FROM order_items WHERE order_id = ?
                    ''', (order_row[0],))
                    
                    items = cursor.fetchall()
                    
                    order_data = {
                        'id': order_row[0],
                        'user_id': order_row[1],
                        'username': order_row[2],
                        'first_name': order_row[3],
                        'customer_name': order_row[4],
                        'customer_phone': order_row[5],
                        'customer_location': order_row[6],
                        'order_data': json.loads(order_row[7]) if order_row[7] else {},
                        'total_amount': order_row[8],
                        'latitude': order_row[9],
                        'longitude': order_row[10],
                        'delivery_fee': order_row[11] or 0,
                        'nearest_branch': order_row[12],
                        'status': order_row[13],
                        'created_at': order_row[14],
                        'updated_at': order_row[15],
                        'items': [
                            {
                                'name': item[0],
                                'quantity': item[1],
                                'total': item[2],
                                'selectedSize': item[3]
                            } for item in items
                        ]
                    }
                    result.append(order_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting recent orders for admin: {e}")
            return []

    def get_total_orders_count(self) -> int:
        """Get total count of orders"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM orders')
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting total orders count: {e}")
            return 0

    def update_order_location_and_fee(self, order_id: int, latitude: float, longitude: float, delivery_fee: int, nearest_branch: str):
        """Update order with location and delivery fee"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE orders 
                    SET latitude = ?, longitude = ?, delivery_fee = ?, nearest_branch = ?
                    WHERE id = ?
                """, (latitude, longitude, delivery_fee, nearest_branch, order_id))
                conn.commit()
                logger.info(f"Updated order {order_id} with location and delivery fee")
        except Exception as e:
            logger.error(f"Error updating order location and fee: {e}")

    def log_admin_access(self, user_id: int, username: str, first_name: str, action: str, details: str = ""):
        """Log admin panel access"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO admin_logs (user_id, username, first_name, action, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, username or '', first_name or '', action, details))
                conn.commit()
                logger.info(f"Admin access logged: {action} by user {user_id}")
        except Exception as e:
            logger.error(f"Error logging admin access: {e}")

    def get_admin_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get admin access logs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM admin_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                logs = cursor.fetchall()
                result = []
                for log_row in logs:
                    log_data = {
                        'id': log_row[0],
                        'user_id': log_row[1],
                        'username': log_row[2],
                        'first_name': log_row[3],
                        'action': log_row[4],
                        'details': log_row[5],
                        'created_at': log_row[6]
                    }
                    result.append(log_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting admin logs: {e}")
            return []

# Global database instance
db = DatabaseManager()
