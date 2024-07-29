import json
import os
import openai
import pandas as pd
import requests

from PIL import Image
from io import BytesIO
import boto3
from fastapi import FastAPI, HTTPException
from models import Diary
from database import AsyncSession



app = FastAPI()

# JSON 파일에서 API 키 불러오기
def load_api_key(filepath):
    with open(filepath, 'r') as file:
        config = json.load(file)
    return config["OPENAI_API_KEY"]

api_key = load_api_key("openai_key.json")
os.environ["OPENAI_API_KEY"] = api_key


# aws 자격 증명 함수
def setup_aws_credentials(aws_file_path):
    credentials_df = pd.read_csv(aws_file_path)
    access_key_id = credentials_df['Access key ID'][0]
    secret_access_key = credentials_df['Secret access key'][0]
    region = credentials_df['AWS_REGION'][0]
    bucket = credentials_df['AWS_S3_BUCKET'][0]
    os.environ["AWS_ACCESS_KEY_ID"] = access_key_id
    os.environ["AWS_SECRET_ACCESS_KEY"] = secret_access_key
    os.environ["AWS_REGION"] = region
    os.environ["AWS_S3_BUCKET"] = bucket



# 일기에서 행동 추출
def extract_behaviors(daily_input):
    behavior = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Please find one behavior in this text. \n "},
                  {"role": "user", "content": daily_input + f'One behavior in this text is : '}],
        temperature=0
    )
    return behavior.choices[0].message.content

# 일기에서 행동 기반 감정 추출
def extract_emotions(daily_input, behaviors):
    emotion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": f"The emotion that you can create well is \
                1. **Happiness**: You can create images that include bright colors, smiling faces, joyful activities, and more. \
                2. **Sadness**: You can create images that reflect dark shades, tears, depressing facial expressions and more. \
                3. **Anger**: It may contain elements such as intense colors, angry expressions, sparks or explosions. \
                4. **Surprise**: You can create images that show wide-eyed expressions, unexpected situations, and more. \
                5. **Calmness**: You can create images that include peaceful landscapes, soft colors, comfortable facial expressions and more. \
                6. **Love (Love)**: It may contain elements that represent intimate relationships, such as heart shapes, lovers or family.\
                7. **Jealous**: It may include uncomfortable expressions, looks at others, situational elements (e.g., scenes where two other people are close together).\
                8. **Anticipation**: This may include excited expressions, gestures, a waiting posture or setting of situations (e.g., how you look with a gift in front of you).\
                9. **Tiredness**: It may indicate yawning, tired expressions, rubbing eyes or feeling sleepy.\
                10. **Stress**: Features include a tense look, a gripping head or hand-to-head position, and an uncomfortable background (e.g. a desk loaded with work).\
                It's 10 like this. In this text, pick 1 out of 10 emotions based on {behaviors}."},
                  {"role": "user", "content": daily_input + f'The emotion under the {behaviors} of this text is '}],
        temperature=0
    )
    return emotion.choices[0].message.content

def generate_image_from_diary(behaviors, emotions):
    
    prompt = f'Asian girl is doing {behaviors}. girl has {emotions} on her face.\
            Everything should be rendered in a simple, sticker-style illustration, \
            characterized by its minimalistic details, bold lines, and flat colors.'
    try:
        images = openai.images.generate(
            model='dall-e-3',
            prompt=prompt,
            n=1,
            quality='standard',
            size="1024x1024"
        )
        return images.data[0].url
    except Exception as e:
        return str(e)

# 이미지를 S3에 업로드하는 함수
def upload_image_to_s3(image_url, bucket_name, object_name):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    s3_client = boto3.client('s3',
                             aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                             aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                             region_name=os.environ["AWS_REGION"]
                             )
    s3_client.upload_fileobj(img_byte_arr, bucket_name, object_name)


async def save_image_name_to_db(diary_id, bucket_name, object_name):
    s3_url = f'https://{bucket_name}.s3.{os.environ["AWS_REGION"]}.amazonaws.com/{object_name}.jpg'

    async with AsyncSession() as session:
        new_image_record = Diary(
            diary_id=diary_id,
            image_url=s3_url
        )

        session.add(new_image_record)
        await session.commit()
    return s3_url

# 메인 처리 함수
async def process_latest_diary_entry(new_diary):
    aws_file_path = 'cloud8-user2_accessKeys.csv'
    setup_aws_credentials(aws_file_path)
    latest_diary = new_diary
    if latest_diary:
        # 일기 내용에서 행동 및 감정 추출
        behaviors = extract_behaviors(latest_diary.content)
        emotions = extract_emotions(latest_diary.content, behaviors)
        # DALL-E를 사용하여 이미지 생성
        image_url = generate_image_from_diary(behaviors, emotions)
        # S3에 이미지 업로드
        bucket_name = os.environ["AWS_S3_BUCKET"]
        date = latest_diary.diary_date
        date = date.replace('-','')
        object_name = f"dalle_images/{date}"

        upload_image_to_s3(image_url, bucket_name, object_name)


        s3_url = f'https://{bucket_name}.s3.{os.environ["AWS_REGION"]}.amazonaws.com/{object_name}.jpg'

        return s3_url
    else:
        return "No diary entries found"

async def dalle_image():
    try:
        # process_latest_diary_entry 함수를 비동기적으로 호출
        image_path = await process_latest_diary_entry()
        if image_path:
            return {"message": "이미지 처리 완료", "image_path": image_path}
        else:
            return {"message": "처리할 일기가 없습니다."}
    except Exception as e:
        # 오류 발생시 HTTP 500 상태 코드로 응답
        raise HTTPException(status_code=500, detail=str(e))