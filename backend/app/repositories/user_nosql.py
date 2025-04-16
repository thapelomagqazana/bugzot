from motor.motor_asyncio import AsyncIOMotorDatabase
from app.repositories.base import BaseRepository
from typing import List, Optional
from app.schemas.user import UserOut
from bson import ObjectId
from app.utils.security import hash_password

class UserNoSQLRepository(BaseRepository[UserOut]):
    """
    User repository for NoSQL databases (MongoDB).
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db["users"]

    async def get_by_id(self, id: str) -> Optional[dict]:
        return await self.db.find_one({"_id": ObjectId(id)})

    async def get_by_email(self, email: str) -> Optional[dict]:
        return await self.db.find_one({"email": email.lower()})

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[dict]:
        return await self.db.find().skip(skip).limit(limit).to_list(length=limit)

    async def create(self, obj_data: dict) -> dict:
        obj_data["hashed_password"] = hash_password(obj_data["password"])
        obj_data.pop("password", None)  # Remove plain password
        result = await self.db.insert_one(obj_data)
        return await self.get_by_id(result.inserted_id)

    async def update(self, id: str, obj_data: dict) -> Optional[dict]:
        await self.db.update_one({"_id": ObjectId(id)}, {"$set": obj_data})
        return await self.get_by_id(id)

    async def delete(self, id: str) -> bool:
        result = await self.db.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
