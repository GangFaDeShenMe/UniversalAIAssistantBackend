from sqlalchemy import Column, Integer

from app.database.connector import Base


class Assistant(Base):
    __tablename__ = 'assistants'

