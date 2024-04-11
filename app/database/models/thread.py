from sqlalchemy import Column, Integer

from app.database.base import Base


class Thread(Base):
    __tablename__ = 'threads'
