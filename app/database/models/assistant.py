from sqlalchemy import Column, Integer

from ..connector import Base


class Assistant(Base):
    __tablename__ = 'assistants'

    id = Column(Integer, primary_key=True)
