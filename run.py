from fastapi import FastAPI, HTTPException, Request, Depends,Query, Body,Path
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import SessionLocal
from pydantic import BaseModel
from models import User, Diary
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
from lamaindex import chatbot,vectordb_input
import models, schemas, crud
import json
import os
import openai
import pandas as pd
import requests
import uvicorn
from PIL import Image
from io import BytesIO
import boto3
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from daily_popup import daily_summary
from keywords import extract_keyword
from emotion import emotion_keyword_extractor
from image_to_db import dalle_image, process_latest_diary_entry


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

# Dependency to get DB session
async def get_db():
    async with SessionLocal() as session:
        yield session

async def update_diary(db: AsyncSession, diary_id: int, diary_data: schemas.DiaryCreate):
    db_diary = await db.get(Diary, diary_id)
    if not db_diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    for var, value in vars(diary_data).items():
        setattr(db_diary, var, value) if value else None
    db.add(db_diary)
    await db.commit()
    await db.refresh(db_diary)
    return db_diary

async def get_diary_by_date(db: AsyncSession, diary_date: str):
    query = select(Diary).where(Diary.diary_date == diary_date)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_summary_db(db: AsyncSession, diary_date: str):
    query = select(Diary).where(Diary.diary_date == diary_date)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def delete_diary(db: AsyncSession, diary_date: str):
    db_diary = await db.get(Diary, diary_date)
    if not db_diary:
        raise HTTPException(status_code=404, detail="Diary not found")
    await db.delete(db_diary)
    await db.commit()
    return {"detail": "Diary deleted"}

##################################################################################################################

# 일기 작성하기
@app.post("/diaries/")
async def create_diary(diary: schemas.DiaryBase, db: AsyncSession = Depends(get_db)):
    # 일기 데이터를 DB에 저장
    new_diary = await crud.create_diary(db=db, diary=diary)
    
    # 요약(summary)이 없는 경우, 요약을 생성
    if not new_diary.summary:
        content = new_diary.content
        new_summary = daily_summary(content)
        new_diary.summary = new_summary
        new_behavior_keyword = extract_keyword(content)
        new_diary.behavior_keyword = new_behavior_keyword
        new_emotion_keyword = emotion_keyword_extractor(content)
        new_diary.emotion_keyword = new_emotion_keyword
        
        db.add(new_diary)
        await db.commit()

    return new_diary
@app.post("/vectorDB/")
async def finalize_diary(user_id: int, db: AsyncSession = Depends(get_db)):
    # DB에서 최신 일기 데이터를 조회
    new_diary = await crud.get_new_diary(db=db, user_id=user_id)
    vectordb_input(new_diary)

@app.post("/diaries/summary/{user_id}")
async def create_summary(user_id: int, db: AsyncSession = Depends(get_db)):
    # DB에서 최신 일기 데이터를 조회
    new_diary = await crud.get_new_diary(db=db,user_id=user_id)
    if new_diary:
        content = new_diary.content
        new_summary = daily_summary(content)
        print(new_summary)
        print(type(new_summary))
        # 기존 Diary 인스턴스를 찾아서 summary를 업데이트
        new_diary.summary = new_summary
        db.add(new_diary)
        await db.commit()
        try:
            # process_latest_diary_entry 함수를 비동기적으로 호출
            image_path = await process_latest_diary_entry(new_diary)
            print(image_path)
            if image_path:
                new_diary.image_url = image_path
                db.add(new_diary)
                await db.commit()
                return {"message": "이미지 처리 완료", "image_path": image_path}
            else:
                return {"message": "처리할 일기가 없습니다."}
        except Exception as e:
            # 오류 발생시 HTTP 500 상태 코드로 응답
            raise HTTPException(status_code=500, detail=str(e))
    
        return {"message": "Diary finalized and processed", "new_summary": new_summary}
    else:
        return {"message": "No diary entries found"}
    
    return await crud.create_diary(db=db, diary=diary)

@app.post("/diaries/behavior_keyword/")
async def create_behavior(user_id: int, db: AsyncSession = Depends(get_db)):
    new_diary = await crud.get_new_diary(db=db, user_id=user_id)    
    if new_diary:
        content = new_diary.content
        new_behavior_keyword = extract_keyword(content)
        new_diary.behavior_keyword = new_behavior_keyword
        db.add(new_diary)
        await db.commit()
        behavior = {"user_id": user_id, "behavior_keyword": new_behavior_keyword}
        return {"message": "Diary finalized and processed", "behavior_keyword": new_behavior_keyword}
    else:
        return {"message": "No diary entries found"}
    #return await crud.create_diary(db=db, diary=diary)    

@app.post("/diaries/emotion_keyword/")
async def create_emotion(user_id: int, db: AsyncSession = Depends(get_db)):
    new_diary = await crud.get_new_diary(db=db, user_id=user_id)    
    if new_diary:
        content = new_diary.content
        new_emotion_keyword = emotion_keyword_extractor(content)
        new_diary.emotion_keyword = new_emotion_keyword
        db.add(new_diary)
        await db.commit()
        emotion = { "user_id": user_id, 
                    "emotion_keyword" :new_emotion_keyword}        
        return {"message": "Diary finalized and processed", "new_emotion_keyword": new_emotion_keyword}
    else:
        return {"message": "No diary entries found"}
    #return await crud.create_diary(db=db, diary=diary)

# @app.post("/dalle-image/{user_id}")
# async def dalle_image(user_id: int, db: AsyncSession = Depends(get_db)):
#     new_diary = await crud.get_new_diary(db=db, user_id=user_id)    
#     print(new_diary)
#     if new_diary:
#         try:
#             # process_latest_diary_entry 함수를 비동기적으로 호출
#             image_path = await process_latest_diary_entry(new_diary)
#             print(image_path)
#             if image_path:
#                 new_diary.image_url = image_path
#                 db.add(new_diary)
#                 await db.commit()
#                 return {"message": "이미지 처리 완료", "image_path": image_path}
#             else:
#                 return {"message": "처리할 일기가 없습니다."}
#         except Exception as e:
#             # 오류 발생시 HTTP 500 상태 코드로 응답
#             raise HTTPException(status_code=500, detail=str(e))
#     else:
#         return {"message": "No diary entries found"}


# @app.post("/emotion_keywords/")
# async def create_emotion(user_id: int, db: AsyncSession = Depends(get_db)):
#     new_diary = await crud.get_new_diary(db=db, user_id=user_id)    
#     if new_diary:
#         content = new_diary.content
#         # 키워드 생성
#         new_emotion_keyword = emotion_keyword_extractor(content)
#         # 기존 Diary 인스턴스를 찾아서 keyword를 업데이트
#         new_diary.extract_keyword = new_emotion_keyword
#         db.add(new_diary)
#         await db.commit()

#         # emotion_emotion_keyword 함수 호출
#         emotion = {"user_id": user_id, "keyword": new_emotion_keyword}
        
#         return {"message": "Diary finalized and processed", "new_emotion_keyword": new_emotion_keyword}
#     else:
#         return {"message": "No diary entries found"}
#     return await crud.create_emotion_keyword(db, emotion)



#######################################################################################################################



# 유저 가져오기
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    return await crud.get_users(db)

# diary_date 통해서 일기 가져오기 없으면 False 띄우기 + image URL 가져오기
@app.get("/diaries/{diary_date}")
async def get_diary(diary_date: str, db: AsyncSession = Depends(get_db)):
    diary = await get_diary_by_date(db=db, diary_date=diary_date)
    if diary:
        return {"exists": True, "diary": diary, "image_url": diary.image_url}
    else:
        return {"exists": False}

# summary 가져오기
@app.get("/diaries/{diary_date}/summary")
async def get_summary(diary_date: str, db: AsyncSession = Depends(get_db)):
    db_summary = await get_summary_db(db=db, diary_date=diary_date)
    return db_summary.summary

@app.get("/chat")
async def chat(request: Request):
    return templates.TemplateResponse("chatbot.html", {"request": request})

@app.post("/submit")
async def submit(chat_request: ChatRequest):
    response = chatbot(chat_request.message)
    return {"response": response}

@app.get('/')
def home():
    #return {'message':'home page'}
    # TODO @kkk 홈페이지 진입시 특정 테스트 페이지로 자동 리다이렉트 처리(임시)
    return RedirectResponse("http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",reload=True)

@app.get("/behavior_keywords/{analysis_date}")
async def read_behavior_keywords(analysis_date: str, db: AsyncSession = Depends(get_db)):
    behavior_keywords = await crud.get_behavior_keywords_by_date(db, analysis_date)
    if not behavior_keywords:
        raise HTTPException(status_code=404, detail="Behavior keywords not found for this date")
    return behavior_keywords

@app.get("/emotion_keywords/{analysis_date}")
async def read_emotion_keywords(analysis_date: str, db: AsyncSession = Depends(get_db)):
    emotion_keywords = await crud.get_emotion_keywords_by_date(db, analysis_date)
    if not emotion_keywords:
        raise HTTPException(status_code=404, detail="emotion_keywords not found for this date")
    return emotion_keywords

# @app.get("/diaries/days/{year}/{month}")
# async def get_diary_date(year: int, month: int, db: AsyncSession = Depends(get_db)):
#     db_diary_date = await get_diary_date_db(db=db, diary_date=diary_date)
#     return db_summary.diary_date

# @app.put("/diary/{user_id}/finalize/")
# async def finalize_diary(user_id: int, db: AsyncSession = Depends(get_db)):
#     # DB에서 최신 일기 데이터를 조회
#     latest_diary = await crud.get_latest_diary(db=db, user_id=user_id)
    # vectordb_input(latest_diary)
    
    # if latest_diary:
    #     content = latest_diary.content
    #     # 요약 생성
    #     new_summary = daily_summary(content)
    #     # 기존 Diary 인스턴스를 찾아서 summary를 업데이트
    #     latest_diary.summary = new_summary
    #     db.add(latest_diary)
    #     await db.commit()
    #     return {"message": "Diary finalized and processed", "new_summary": new_summary}
    # else:
    #     return {"message": "No diary entries found"}
    
    # if latest_diary:
    #     # 비동기 함수 호출로 키워드 추출
    #     new_keyword = extract_keyword(latest_diary.content)
    #     async with AsyncSession() as session:
    #         # latest_diary의 diary_id와 일치하는 Behavior 인스턴스를 찾음
    #         result = await session.execute(select(Behavior).where(Behavior.diary_id == latest_diary.diary_id))
    #         behavior_entry = result.scalar_one_or_none()
    #         #print(behavior_entry.behaviorKeyword)
    #         # 해당 Behavior 인스턴스가 있는 경우 키워드 업데이트
    #         if behavior_entry:
    #             behavior_entry.BehaviorKeyword = new_keyword

    #         # 해당 Behavior 인스턴스가 없는 경우 새로운 인스턴스 생성
    #         else:
    #             behavior_entry = Behavior(
    #                 diary_id=latest_diary.diary_id,
    #                 behaviorKeyword=new_keyword
    #             )
    #             session.add(behavior_entry)

    #         # 세션에 커밋
    #         await session.commit()
    #         return new_keyword
    # else:
    #     return "No diary entries found"
        
# @app.put("/diary/{user_id}/finalize/")
# async def finalize_diary(user_id: int, db: AsyncSession = Depends(get_db)):
#     # DB에서 최신 일기 데이터를 조회
#     latest_diary = await crud.get_latest_diary(db=db, user_id=user_id)
#     vectordb_input(latest_diary)
    
    # if latest_diary:
    #     content = latest_diary.content
    #     # 요약 생성
    #     new_summary = daily_summary(content)
    #     # 기존 Diary 인스턴스를 찾아서 summary를 업데이트
    #     latest_diary.summary = new_summary
    #     db.add(latest_diary)
    #     await db.commit()
    #     return {"message": "Diary finalized and processed", "new_summary": new_summary}
    # else:
    #     return {"message": "No diary entries found"}

# # diary_date 통해서 일기 업데이트하기
# @app.put("/diaries/{diary_date}")
# async def update_diary_endpoint(diary_date: str, diary: schemas.DiaryCreate, db: AsyncSession = Depends(get_db)):
#     return await crud.update_diary(db=db, diary_date=diary_date, diary=diary)

# # diary_date 통해서 일기 삭제하기
# @app.delete("/diaries/{diary_date}")
# async def delete_diary_endpoint(diary_date: str, db: AsyncSession = Depends(get_db)):
#     return await crud.delete_diary(db=db, diary_date=diary_date)

# @app.get("/diaries/")
# async def read_latest_diary(db: AsyncSession = Depends(get_db)):
#     latest_diary = await get_latest_diary(db)
#     if latest_diary is None:
#         raise HTTPException(status_code=404, detail="No latest diary found")
#     return latest_diary

    # async def update_diary(db: AsyncSession, diary_date: str, diary_data: schemas.DiaryCreate):
#     db_diary = await db.get(Diary, diary_date)
#     if not db_diary
#         raise HTTPException(status_code=404, detail="Diary not found")
#     for var, value in vars(diary_data).items():
#         setattr(db_diary, var, value) if value else None
#     db.add(db_diary)
#     await db.commit()
#     await db.refresh(db_diary)
#     return db_diary

    # uvicorn run:app --reload