# /telemetry-service/app/repositories/base.py
from typing import Generic, TypeVar, Type
from sqlalchemy.orm import Session

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model