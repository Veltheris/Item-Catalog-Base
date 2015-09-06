import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
"""
Setup for the Item Catalog Application
"""

#Define our own tables
Base = declarative_base()

#The Users Table
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key = True)
    name = Column(String(80), nullable = False)
    email = Column(String(80), nullable = False)
    picture = Column(String(120), nullable = False)
    
#Categories for items to go in
class Category(Base):
    __tablename__ = 'category'
    name = Column(String(80), unique = True)
    id = Column(Integer, primary_key = True)
    public = Column(Boolean, default = True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, single_parent=True, cascade="delete, delete-orphan")

#The items themselves. The Picture only refers to a pointer, rather than storing the image itself.
#There is a lot of debate on the internet about how to store images...

class Item(Base):
    __tablename__ = 'item'
    name = Column(String(80),nullable = False, primary_key = True)
    description = Column(String(250))
    category_id = Column(String(80), ForeignKey('category.id'))
    category = relationship(Category, single_parent=True, cascade="delete, delete-orphan")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User, single_parent=True, cascade="delete, delete-orphan")
    picture = Column(String(80))
    changed = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

###### END OF FILE ######

engine = create_engine('postgresql://@/catalog')

Base.metadata.create_all(engine)
