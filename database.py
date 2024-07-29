from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv #.env 파일 로드
from urllib.parse import quote
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base

load_dotenv('.env') #.env 파일 로드

user        = os.getenv('DB_USER') # 환경변수 변수에 저장
password    = quote(os.getenv('DB_PASSWORD'))
host        = os.getenv('DB_HOST') 
port        = os.getenv('DB_PORT')
dbname      = os.getenv('DB_NAME')

DB_URL      = f'mysql+aiomysql://{user}:{password}@{host}:{port}/{dbname}'
engine      = create_async_engine(DB_URL)


class engineconn:
    def __init__(self):
        self.engine = create_engine(DB_URL, pool_recycle = 500)
    def sessionmaker(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session
    def connection(self):
        conn = self.engine.connect()
        return conn
_engine         = create_async_engine(DB_URL)
SessionLocal    = sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)
Base            = declarative_base()


# print( 'DB_URL => ', DB_URL) 