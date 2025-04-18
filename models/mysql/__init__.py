import pymysql
import os
from flask import g

def get_db_connection():
    if 'db' not in g:
        g.db = pymysql.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_NAME'),
            charset='utf8'
        )
    return g.db

def get_cursor():
    db = get_db_connection()
    if 'cursor' not in g:
        g.cursor = db.cursor()
    return g.cursor