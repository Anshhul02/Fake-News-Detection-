from motor.motor_asyncio import AsyncIOMotorClient

from backend.config import settings


client = AsyncIOMotorClient(settings.mongodb_url)

db = client[settings.database_name]


# Collections
users_collection = db["users"]
predictions_collection = db["predictions"]


async def connect_to_database():
    await client.admin.command("ping")
    print("MongoDB connected successfully")


async def close_database_connection():
    client.close()
    print("MongoDB connection closed")