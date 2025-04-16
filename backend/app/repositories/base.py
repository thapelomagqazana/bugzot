from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")  # Represents any data model

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for all repositories.
    Defines CRUD operations that should be implemented.
    """

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass

    @abstractmethod
    def create(self, obj_data: dict) -> T:
        pass

    @abstractmethod
    def update(self, id: int, obj_data: dict) -> Optional[T]:
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        pass
