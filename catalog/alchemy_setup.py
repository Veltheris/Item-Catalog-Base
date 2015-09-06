import datetime
#from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import relationship
#from sqlalchemy import create_engine
"""
Setup for the Item Catalog Application
"""
from flask import Flask
#from application import app
from flask.ext.sqlalchemy import SQLAlchemy

#engine = create_engine('postgresql://@/catalog')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://@/catalog'
db = SQLAlchemy(app)


#Define our own tables
#Base = declarative_base()

#The Users Table
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), nullable = False)
    email = db.Column(db.String(80), nullable = False)
    picture = db.Column(db.String(120), nullable = False)
    
#Categories for items to go in
class Category(db.Model):
    __tablename__ = 'category'
    name = db.Column(db.String(80), unique = True)
    id = db.Column(db.Integer, primary_key = True)
    public = db.Column(db.Boolean, default = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User, single_parent=True, cascade="delete, delete-orphan")

#The items themselves. The Picture only refers to a pointer, rather than storing the image itself.
#There is a lot of debate on the internet about how to store images...

class Item(db.Model):
    __tablename__ = 'item'
    name = db.Column(db.String(80),nullable = False, primary_key = True)
    description = db.Column(db.String(250))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(Category, single_parent=True, cascade="delete, delete-orphan")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User, single_parent=True, cascade="delete, delete-orphan")
    picture = db.Column(db.String(80))
    changed = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

###### END OF FILE ######

#engine = create_engine('postgresql://@/catalog')

#Base.metadata.create_all(engine)

if __name__ == '__main__':
    db.create_all()
