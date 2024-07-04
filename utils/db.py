from flask_pymongo import PyMongo

def init_db(app):
    mongo = PyMongo(app)
    mongo.db.create_collection('users')
    return mongo

