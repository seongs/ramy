import json
import os
import openai
from fastapi import FastAPI
from models import Diary
from database import SessionLocal
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()


# 가장 최신의 일기 항목 가져오는 함수
async def get_latest_diary():
    async with AsyncSession() as session:
        result = await session.execute(
            select(Diary).order_by(Diary.diary_date.desc()).limit(1)
        )
        return result.scalars().first()



# JSON 파일에서 API 키 불러오기
def load_api_key(filepath):
    with open(filepath, 'r') as file:
        config = json.load(file)
    return config["OPENAI_API_KEY"]


# 키워드 추출
def extract_keyword(document):
    api_key = load_api_key("openai_key.json")
    os.environ["OPENAI_API_KEY"] = api_key
    prompt = """
    예시:
    일기: '오늘은 친구들과 영화를 보러 갔다. 영화관에서 팝콘을 먹으며 즐거운 시간을 보냈다.'
    키워드: '영화'

    일기: '비가 오는 날이었지만, 우산을 쓰고 산책을 나갔다. 공원의 빗소리가 정말 평화로웠다.'
    키워드: '산책'

    일기: '오늘은 조금 느긋한 하루였어. 아침에는 집에서 요리를 했는데, 건강을 생각해서 샐러드와 오트밀을 만들었어. 오후에는 용산구 근처에 있는 소품샵을 구경했어. 다양한 핸드메이드 소품들이 정말 예뻤어. 거기서 감성적인 노트와 컬러풀한 펜을 몇 개 샀어. 친구들과 버블티를 마시며 수다를 떨었는데, 정말 즐거웠어. 집에 돌아와서는 조용히 책을 읽으며 하루를 마무리했어.'
    키워드: '소품샵'

    일기: '주말이라 집에서 편안하게 보냈어. 아침에는 잠깐 산책을 하고, 오후엔 새로운 다이어트 레시피를 시도해봤어. 저녁에는 온라인으로 친구들과 게임 대회를 했는데, 엄청 재미있었어. 밤에는 좋아하는 음악을 들으며 휴식을 취했지.'
    키워드: '게임'

    일기: 
    """ + document + "\n키워드: "
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "이 다음 텍스트에서 주요 키워드를 하나만 추출합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0
        )

        # 모델 응답에서 주요 키워드 추출
        return (response.choices[0].message.content)
    except Exception as e:
        # API 호출 실패시 예외 처리
        return f"Error extracting keyword: {str(e)}"