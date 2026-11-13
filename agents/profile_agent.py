# import sqlite3
# import hashlib
# import os
# from pathlib import Path

# PROJECT_DIR = Path(__file__).resolve().parents[1]
# DB_PATH = PROJECT_DIR / "data" / "irctc.db"

# def connect_db():
#     DB_PATH.parent.mkdir(parents=True, exist_ok=True)
#     return sqlite3.connect(DB_PATH)


# def create_tables():
#     with connect_db() as connection:

#         # Store registered user accounts.
#         connection.execute("""
#             CREATE TABLE IF NOT EXISTS users(
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT UNIQUE NOT NULL,
#                 password_hash TEXT NOT NULL,
#                 passenger_name TEXT NOT NULL
#             )
#         """)

#         # Store bookings belonging to each registered user.
#         connection.execute("""
#             CREATE TABLE IF NOT EXISTS bookings(
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 user_id INTEGER NOT NULL,
#                 passenger_name TEXT NOT NULL,
#                 train_number TEXT NOT NULL,
#                 source TEXT NOT NULL,
#                 destination TEXT NOT NULL,
#                 journey_date TEXT NOT NULL,
#                 travel_class TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 FOREIGN KEY (user_id) REFERENCES users(id)
#             )
#         """)

        
# def hash_password(password):
#     salt = os.urandom(16)
#     password_hash = hashlib.pbkdf2_hmac(
#         "sha256", password.encode(), salt, 200000
#     )
#     return salt.hex() + ":" + password_hash.hex()

# def verify_password(password, stored_hash):
#     salt_hex, hash_hex = stored_hash.split(":")
    
#     password_hash = hashlib.pbkdf2_hmac(
#         "sha256", password.encode(), bytes.fromhex(salt_hex), 200000
#     )
#     return password_hash.hex() == hash_hex

# def register_user(username, password, passenger_name):
#     create_tables()
    
#     try:
#         with connect_db() as connection:
#             connection.execute(
#                 "INSERT INTO users(username, password_hash, passenger_name )"
#                 "VALUES(?, ?, ?)",
#                 (username, hash_password(password), passenger_name)
#             )
#         return {"success": True, "messages": "Account created"}
#     except sqlite3.IntegrityError:
#         return {"success": False, "messages": "Username already exists"}
    
# def login_user(username,password):
#     create_tables()
#     with connect_db() as connection:
#         user = connection.execute(
#             "SELECT id, password_hash, passenger_name "
#             "FROM users WHERE username = ?",
#             (username,)
#         ).fetchone()
    
#     # reject unknown username and password    
#     if user is None or not verify_password(password, user[1]): 
#         return {"success": False, "message": "Invalid username or password"}
    
#     return{
#         "success": True,
#         "user_id": user[0],
#         "username": username,
#         "passenger_name": user[2]
#     }
    

# def save_booking(user_id, booking):

#     create_tables()

#     with connect_db() as connection:
#         cursor = connection.execute("""
#             INSERT INTO bookings(
#                 user_id,
#                 passenger_name,
#                 train_number,
#                 source,
#                 destination,
#                 journey_date,
#                 travel_class,
#                 status
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#         """, (
#             user_id,
#             booking["passenger"],
#             booking["train_number"],
#             booking["source"],
#             booking["destination"],
#             booking["journey_date"],
#             booking["travel_class"],
#             booking["status"]
#         ))

#         return {
#             "success": True,
#             "booking_id": cursor.lastrowid,
#             "messages": "Booking saved successfully"
#         }


# def get_booking_history(user_id):

#     create_tables()

#     with connect_db() as connection:
#         rows = connection.execute("""
#             SELECT id, train_number, source, destination,
#                    journey_date, travel_class, status, created_at
#             FROM bookings
#             WHERE user_id = ?
#             ORDER BY created_at DESC
#         """, (user_id,)).fetchall()

#     # Convert database rows into dictionaries for easier use.
#     columns = [
#         "booking_id", "train_number", "source", "destination",
#         "journey_date", "travel_class", "status", "created_at"
#     ]

#     return [dict(zip(columns, row)) for row in rows]



import sqlite3
import hashlib
import hmac
import os
from pathlib import Path
from contextlib import contextmanager

# Locate the database inside this project.
PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "irctc.db"


@contextmanager
def connect_db():
    """Open a database connection and close it after use."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)

    # Enable foreign-key checking for this connection.
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_tables():
    """Create all database tables without deleting existing records."""

    with connect_db() as connection:

        # Registered passenger accounts.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                passenger_name TEXT NOT NULL
            )
        """)

        # Simulated ticket bookings.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                passenger_name TEXT NOT NULL,
                train_number TEXT NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                journey_date TEXT NOT NULL,
                travel_class TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Simulated food orders.
        connection.execute("""
            CREATE TABLE IF NOT EXISTS food_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                passenger_name TEXT NOT NULL,
                train_number TEXT NOT NULL,
                journey_date TEXT NOT NULL,
                delivery_station TEXT NOT NULL,
                food_item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)


def hash_password(password):
    """Hash a password using PBKDF2 and a random salt."""

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        200000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password, stored_hash):
    """Check whether the entered password matches the stored hash."""

    try:
        salt_hex, hash_hex = stored_hash.split(":")

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            200000
        )

        # Compare hashes safely.
        return hmac.compare_digest(password_hash.hex(), hash_hex)

    except (ValueError, TypeError):
        return False


def register_user(username, password, passenger_name):
    """Create a new passenger account."""

    if not all([username, password, passenger_name]):
        return {
            "success": False,
            "message": "All registration fields are required."
        }

    create_tables()

    try:
        with connect_db() as connection:
            connection.execute(
                """
                INSERT INTO users(username, password_hash, passenger_name)
                VALUES (?, ?, ?)
                """,
                (username, hash_password(password), passenger_name)
            )

        return {
            "success": True,
            "message": "Account created successfully."
        }

    except sqlite3.IntegrityError:
        return {
            "success": False,
            "message": "Username already exists."
        }

    except sqlite3.Error:
        return {
            "success": False,
            "message": "Unable to create account."
        }


def login_user(username, password):
    """Authenticate a passenger using their username and password."""

    create_tables()

    try:
        with connect_db() as connection:
            user = connection.execute(
                """
                SELECT id, password_hash, passenger_name
                FROM users
                WHERE username = ?
                """,
                (username,)
            ).fetchone()

        if user is None or not verify_password(password, user[1]):
            return {
                "success": False,
                "message": "Invalid username or password."
            }

        return {
            "success": True,
            "user_id": user[0],
            "username": username,
            "passenger_name": user[2],
            "message": "Login successful."
        }

    except sqlite3.Error:
        return {
            "success": False,
            "message": "Unable to access the account database."
        }


def save_booking(user_id, booking):
    """Save a simulated ticket booking for a passenger."""

    create_tables()

    try:
        with connect_db() as connection:
            cursor = connection.execute(
                """
                INSERT INTO bookings(
                    user_id, passenger_name, train_number,
                    source, destination, journey_date,
                    travel_class, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    booking["passenger"],
                    booking["train_number"],
                    booking["source"],
                    booking["destination"],
                    booking["journey_date"],
                    booking["travel_class"],
                    booking["status"]
                )
            )

            booking_id = cursor.lastrowid

        return {
            "success": True,
            "booking_id": booking_id,
            "message": "Booking saved successfully."
        }

    except (sqlite3.Error, KeyError, TypeError):
        return {
            "success": False,
            "message": "Unable to save booking."
        }


def get_booking_history(user_id):
    """Retrieve all ticket bookings belonging to one passenger."""

    create_tables()

    with connect_db() as connection:
        rows = connection.execute(
            """
            SELECT id, train_number, source, destination,
                   journey_date, travel_class, status, created_at
            FROM bookings
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

    columns = [
        "booking_id", "train_number", "source", "destination",
        "journey_date", "travel_class", "status", "created_at"
    ]

    return [dict(zip(columns, row)) for row in rows]


def save_food_order(user_id, order):
    """Save a simulated food order for a passenger."""

    create_tables()

    try:
        quantity = int(order["quantity"])

        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        with connect_db() as connection:
            cursor = connection.execute(
                """
                INSERT INTO food_orders(
                    user_id, passenger_name, train_number,
                    journey_date, delivery_station, food_item,
                    quantity, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    order["passenger"],
                    order["train_number"],
                    order["journey_date"],
                    order["delivery_station"],
                    order["food_item"],
                    quantity,
                    order["status"]
                )
            )

            order_id = cursor.lastrowid

        return {
            "success": True,
            "order_id": order_id,
            "message": "Food order saved successfully."
        }

    except (sqlite3.Error, KeyError, TypeError, ValueError):
        return {
            "success": False,
            "message": "Unable to save food order."
        }


def get_food_order_history(user_id):
    """Retrieve food orders belonging to one passenger."""

    create_tables()

    with connect_db() as connection:
        rows = connection.execute(
            """
            SELECT id, train_number, journey_date,
                   delivery_station, food_item, quantity,
                   status, created_at
            FROM food_orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,)
        ).fetchall()

    columns = [
        "order_id", "train_number", "journey_date",
        "delivery_station", "food_item", "quantity",
        "status", "created_at"
    ]

    return [dict(zip(columns, row)) for row in rows]


# Create the tables when this module is run directly.
if __name__ == "__main__":
    create_tables()
    print("Database tables are ready.")

