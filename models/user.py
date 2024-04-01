from sqlalchemy import Column, String, Integer, Boolean
from sql_app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    social_type = Column(String)
    access_token = Column(String)
    password = Column(String)
    is_verified = Column(Boolean)
    verification_code = Column(Integer)