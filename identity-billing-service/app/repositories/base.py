# /identity-billing-service/app/repositories/base.py
from typing import TypeVar, Generic, Type
from sqlalchemy.orm import Session
from app.core.database import Base

# Define a generic type variable that binds to our SQLAlchemy Base
ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: int) -> ModelType | None:
        """Retrieves a single record by its primary key ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, obj_in: ModelType) -> ModelType:
        """Adds a new record to the database and commits the transaction."""
        self.db.add(obj_in)
        self.db.commit()
        self.db.refresh(obj_in)
        return obj_in

    def delete(self, id: int) -> bool:
        """Deletes a record by its ID."""
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False