from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import models, schemas
from models import Behavior, Emotion,Diary

async def create_diary(db: AsyncSession, diary: schemas.DiaryCreate):
    db_diary = models.Diary(**diary.dict())
    db.add(db_diary)
    await db.commit()
    await db.refresh(db_diary)
    return db_diary



async def get_behavior_keywords_by_date(db: AsyncSession, analysis_date: str):
    query = select(Behavior.behavior_keyword).where(Behavior.analysis_date == analysis_date)
    result = await db.execute(query)
    return result.scalars().all()

async def get_emotion_keywords_by_date(db: AsyncSession, analysis_date: str):
    query = select(Emotion.emotion_keyword).where(Emotion.analysis_date == analysis_date)
    result = await db.execute(query)
    return result.scalars().all()    


async def get_summary(db: AsyncSession, diary_date: str):
    # diary_date를 기반으로 데이터베이스에서 일기 검색
    result = await db.execute(
        select(Diary).where(Diary.date == diary_date)
    )
    diary_entry = result.scalar_one_or_none()

    if diary_entry is None:
        return None
    return diary_entry.summary


async def get_new_diary(db: AsyncSession, user_id : int):
    # Diary 모델에서 가장 최근의 일기를 조회합니다.
    result = await db.execute(
        select(models.Diary).order_by(desc(models.Diary.created_at)).limit(1)
    )
    # 첫 번째 결과를 반환합니다. 일치하는 결과가 없으면 None을 반환합니다.
    return result.scalar_one_or_none()


# Read a diary entry by id
async def get_diary(db: AsyncSession, diary_date: str):
    stmt = select(models.Diary).where(models.Diary.diary_date == diary_date)
    result = await db.execute(stmt)
    db_diary = result.scalar_one_or_none()
    return db_diary