import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    thrown_bricks = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    thrown_armatures = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    fixed = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    dodges = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    thrown_sands = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    thrown_cements = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    kills = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    hits = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    get_items = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    wins = sqlalchemy.Column(sqlalchemy.Integer, default=0)
