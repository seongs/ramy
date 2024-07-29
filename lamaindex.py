import json
from llama_index import GPTVectorStoreIndex, ServiceContext, LLMPredictor,PromptHelper, ServiceContext, StorageContext,SimpleDirectoryReader
from llama_index.vector_stores import PineconeVectorStore
import pandas as pd
import os
import pymysql
import pymysql.cursors
import pinecone
from dotenv import load_dotenv
from llama_index.llms import OpenAI
import models
from datetime import datetime



current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d")


file_path = '\\data\\'

with open('openai_key.json', 'r') as file:
    config_open = json.load(file)
openai_key =config_open["OPENAI_API_KEY"]



with open('pinecone.json', 'r') as file:
    config_pc = json.load(file)

pc_key=config_pc["PC_API_KEY"]
pc_env=config_pc["PC_ENV"]
pc_name=config_pc["PC_NAME"]







# JSON 파일에서 API 키 불러오기




# #문서 로드 함수
# def load_documents(directory):
#     return SimpleDirectoryReader(directory).load_data()

# #일기 텍스트 추출
# def get_daily_text(date_input):
#     diary_text = pd.read_csv('/Diaty_db(2023.12).csv')

#     try:
#         # 입력된 날짜를 구성 요소로 분리 (년, 월, 일)
#         year, month, day = map(int, date_input.split('-'))

#         # 날짜 형식을 맞춤 (예: "2023년 9월 1일")
#         formatted_date = f"{year}년 {month}월 {day}일"

#         # 해당 날짜에 해당하는 일기 찾기
#         entry = diary_text[diary_text['DATE'] == formatted_date]

#         if not entry.empty:
#             daily_input = entry.iloc[0]['CONTENT']
#             return daily_input
#         else:
#             return "해당 날짜에 일기가 없습니다."
#     except ValueError:
#         return "날짜 형식이 잘못되었습니다. 'YYYY-MM-DD' 형식으로 입력해주세요."

# #색인 생성 함수
# def create_index(documents):
#     return VectorStoreIndex.from_documents(documents)

# #쿼리 엔진 생성 및 쿼리 실행 함수
# def query_index(index, query):
#     query_engine = index.as_query_engine()
#     return query_engine.query(query)

def chatbot(input):

    # API 키 설정
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["PINECONE_API_KEY"] = pc_key

    pinecone.init(
	environment=pc_env,
    )
    index = pinecone.Index(pc_name)
    vector_store = PineconeVectorStore(pinecone_index=index) # 파인콘 벡터 스토어 불러오기
    index = GPTVectorStoreIndex.from_vector_store(vector_store)# 라마인덱스에 파인콘 벡터스토어 연결
    query_engine = index.as_query_engine() # 질의 변수 입력
    
    # 현재 날짜와 시간을 가져옵니다.
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
    response = query_engine.query(
        f'현재 날짜: {formatted_datetime}\
        일기 작성자 & 챗봇 질문자 이름: 성열\
        제공한 데이터는 사용자가 직접 쓴 일기데이터야\
        사용자의 질문에 대한 대답은 존댓말로 해줘\
        일기 데이터를 기반으로\
        사용자의 질문:{input}'
        )
    return response.response

def vectordb_input(diary):
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["PINECONE_API_KEY"] = pc_key
    
    # Diary 객체에서 content 속성만 추출
    content_data = {"content": diary.content}

    # DataFrame 생성
    df = pd.DataFrame([content_data])
    df.to_csv(file_path +f'dairy_{formatted_time}.csv') #csv파일 생성
    documents=SimpleDirectoryReader(file_path).load_data() #csv파일 읽기
    llm_pre = LLMPredictor(llm=OpenAI(temperature=0.3)) # openai파라미터 설정
    prompt_helper = PromptHelper(chunk_size_limit=400)# 청크 수 분할설정
    service_context = ServiceContext.from_defaults(llm_predictor=llm_pre,prompt_helper=prompt_helper)
    vector_store = PineconeVectorStore(index_name=pc_name,environment=pc_env) # pinecone설정
    storage_context = StorageContext.from_defaults(vector_store=vector_store) # 벡터스토리지 연결
    GPTVectorStoreIndex.from_documents( documents, storage_context= storage_context,service_context=service_context) # 벡터화 후 입력
   