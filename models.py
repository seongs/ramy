from sqlalchemy import Column, Integer,String,DateTime,Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()

class User(Base):
    __tablename__ = "user"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255),index= True,nullable=False)
    password = Column(String(255),index=True,nullable=False)
    name = Column(String(50),index=True,nullable=False)
    nickname = Column(String(50), index=True,nullable=False)
    gender = Column(String(1), index=True,nullable=False)
    created_at = Column(DateTime,nullable=True)
    member_status = Column(String(25),nullable=True,default='MEMBER_ACTIVE')
    profile_image = Column(String(255),nullable=True)

class Diary(Base):
    __tablename__ = "diary"

    diary_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer,index= True,nullable=False)
    content = Column(Text,index=True,nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),index=True,nullable=False)
    diary_date = Column(String, index=True,nullable=False)
    summary = Column(String,index=True,nullable=False)
    image_url = Column(String,index=True,nullable=False)
    behavior_keyword = Column(String,index=True,nullable=False)
    emotion_keyword = Column(String,index=True,nullable=False)

class Emotion(Base):
    __tablename__ = "emotion_keywords"

    emotion_id = Column(Integer, primary_key=True, autoincrement=True)
    diary_id = Column(Integer,index= True,nullable=False)
    emotion_keyword = Column(String,index=True,nullable=False)
    analysis_date = Column(String, index=True,nullable=False)
    user_id = Column(Integer,index= True,nullable=False)

class Behavior(Base):
    __tablename__ = 'behavior_keywords'

    behavior_id = Column(Integer,primary_key=True, autoincrement=True)
    diary_id = Column(Integer, index=True,nullable=False)
    behavior_keyword = Column(String,index=True,nullable=False)
    analysis_date = Column(String,index=True,nullable=False)
    user_id = Column(Integer,index= True,nullable=False)

class Dalle(Base):
    __tablename__ = "dalle_Image"

    Dalle_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer,index= True,nullable=False)
    image_path = Column(Text,index=True,nullable=False)
    creation_date = Column(DateTime,index=True,nullable=False)
    behavior = Column(String, index=True, nullable=False)
    emotion = Column(String, index=True, nullable=False)

class Chat_Conversation(Base):
    __tablename__ = "chat_conversation"
    conversation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, autoincrement=True)
    bot_response = Column(DateTime, nullable=False)
    user_input = Column(DateTime, nullable=False)
    conversation = Column(String, nullable=False)

class Analysis(Base):
    __tablename__ = "analysis"
    analysis_id = Column(Integer,index= True, primary_key=True,nullable=False)
    behavior_url = Column(String, index=True, nullable=False)
    emotion_url = Column(String, index=True, nullable=False)