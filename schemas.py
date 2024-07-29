from pydantic import BaseModel
from datetime import datetime

class SomeModel(BaseModel):
    some_datetime_field: datetime

class DiaryBase(BaseModel):
    diary_id: int | None = None
    user_id: int
    content : str
    created_at : datetime
    summary:str | None = None
    diary_date : str
    image_url : str | None = None
    behavior_keyword : str | None = None
    emotion_keyword :str | None = None
    class Config:
        arbitrary_types_allowed = True

class DiaryCreate(DiaryBase):
    pass

class Diary(DiaryBase):
    diary_id: int

    class Config:
        orm_mode = True

# class Behavior(BaseModel):
#     behavior_id : int
#     diary_id : int
#     behavior_keyword : str
#     analysis_date : str
#     user_id: int

# class Emotion(BaseModel):
#     emotion_id : int
#     diary_id : int
#     emotion_keyword :str
#     analysis_date : str
#     user_id: int
