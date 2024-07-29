import json
import os
import openai
import uvicorn
from database import AsyncSession
from models import Diary
from sqlalchemy.future import select
from crud import get_new_diary

# JSON 파일에서 API 키 불러오기
def load_api_key(filepath):
    with open(filepath, 'r') as file:
        config = json.load(file)
    return config["OPENAI_API_KEY"]



# 일간 한줄 분석 함수
def daily_summary(document):
    api_key = load_api_key("openai_key.json")
    os.environ["OPENAI_API_KEY"] = api_key
    prompt = """
        예시:
        일기: '새해 첫 월요일! 오늘은 방학이라 시간이 많아서 좋다. 카페에 가서 친구랑 수다를 떨었어. 오랜만에 만나서 이야기할 게 많았지. 친구가 추천해준 코트를 인터넷으로 구경하다가, 나도 모르게 구매 버튼을 눌렀어. 새 옷이 기대돼!'
        요약: '방학 기념으로 기쁘게 친구와 수다를 떨었고, 친구의 추천으로 코트를 구매해서 설레임을 느꼈어.'

        일기: '토요일이라 드디어 새로 산 코트를 입고 나갔어. 날씨도 화창해서 기분이 좋았지. 혼자 동네를 돌아다니며 예쁜 가게들을 구경했어. 집 근처 작은 갤러리에 들러 전시 작품들을 감상했는데, 나도 언젠가 이런 작품을 만들 수 있으면 좋겠다는 생각이 들었어.'
        요약: '새로 산 코트를 입고 동네를 돌아다니며 예쁜 가게들을 구경하고 작품 감상하며 창작욕구를 느꼈어.'

        일기: '오늘은 조금 이른 아침에 일어나서 캠퍼스 주변을 산책했어. 이른 봄의 신선한 공기가 기분을 상쾌하게 해줬지. 학교에서는 디자인 프로젝트에 대한 새로운 아이디어가 떠올라서 바로 스케치북에 그려봤어. 오후에는 도서관에서 과제를 마무리하고, 저녁엔 가벼운 요리를 해서 혼자 식사를 했어. 밤에는 좋아하는 밴드 음악을 들으며 하루를 정리했지.'
        요약: '오늘은 캠퍼스 산책으로 상쾌한 기분을 느끼고, 디자인 프로젝트에 대한 새로운 아이디어로 흥분했어.'

        일기: """ + document + "\n요약: "

    response = openai.chat.completions.create(
        model="gpt-4",  # 모델 지정
        messages=[
            {"role": "system", "content": "Please summarize this text in one line. To include 1 major event and 1 emotion related to the event. In Korean"},
            {"role": "user", "content": prompt}
        ],
        temperature = 0
    )

    return (response.choices[0].message.content)


    


      




