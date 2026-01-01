"""
Simple user creation script using bcrypt directly
"""
import asyncio
from getpass import getpass
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "conversation_db")


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    # Convert to bytes and truncate to 72 bytes
    password_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


async def create_user():
    """Create user"""
    print("\n" + "="*50)
    print("🚀 Abbotsford User Creation (Simple)")
    print("="*50 + "\n")
    
    # Get input
    email = input("📧 Email: ").strip()
    if not email or "@" not in email:
        print("❌ Invalid email")
        return
    
    password = getpass("🔒 Password: ")
    if len(password) < 6:
        print("❌ Password must be at least 6 characters")
        return
    
    password_confirm = getpass("🔒 Confirm: ")
    if password != password_confirm:
        print("❌ Passwords don't match")
        return
    
    name = input("👤 Name: ").strip()
    if not name:
        print("❌ Name required")
        return
    
    role = input("🎭 Role (user/admin) [user]: ").strip().lower() or "user"
    
    # Collect additional details for regular users
    phone = None
    country = None
    city = None
    coffee_style = None
    current_serving_capacity = None
    
    if role == "user":
        print("\n📋 Additional Customer Details:")
        phone = input("📞 Phone (with country code, e.g., +919686036342): ").strip() or None
        country = input("🌍 Country: ").strip() or None
        city = input("🏙️  City: ").strip() or None
        coffee_style = input("☕ Coffee Style (e.g., Bold, Mild, Specialty): ").strip() or None
        capacity_input = input("📊 Current Serving Capacity (cups/day): ").strip()
        if capacity_input:
            try:
                current_serving_capacity = int(capacity_input)
            except ValueError:
                print("⚠️  Invalid capacity, skipping...")
                current_serving_capacity = None
    
    # Connect to MongoDB
    print("\n⏳ Connecting...")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    
    try:
        # Check if exists
        existing = await db.users.find_one({"email": email})
        if existing:
            print(f"❌ User '{email}' already exists")
            return
        
        # Hash password
        hashed = hash_password(password)
        
        # Create user document
        user = {
            "email": email,
            "password": hashed,
            "name": name,
            "role": role,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Add additional fields for regular users
        if role == "user":
            user.update({
                "phone": phone,
                "country": country,
                "city": city,
                "coffee_style": coffee_style,
                "current_serving_capacity": current_serving_capacity
            })
        
        result = await db.users.insert_one(user)
        
        print("\n" + "="*50)
        print("✅ User created!")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"👤 Name: {name}")
        print(f"🎭 Role: {role}")
        print(f"🆔 ID: {result.inserted_id}")
        
        if role == "user":
            print("\n📋 Customer Details:")
            if phone:
                print(f"📞 Phone: {phone}")
            if country:
                print(f"🌍 Country: {country}")
            if city:
                print(f"🏙️  City: {city}")
            if coffee_style:
                print(f"☕ Coffee Style: {coffee_style}")
            if current_serving_capacity:
                print(f"📊 Serving Capacity: {current_serving_capacity} cups/day")
        
        print("\n💡 You can now login!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(create_user())
