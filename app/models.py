# app/models.py
from sqlalchemy import Column, Integer, String, Text
from app.db import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(255), nullable=False)
    site = Column(String(255), nullable=True)
    contact = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Project id={self.id} client_name={self.client_name!r}>"
