import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().with_name(".env"))

LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL") or "http://localhost:8000/v1"
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME") or "qwen3"
API_KEY = os.getenv("OPENAI_API_KEY") or "not-needed"
BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.deepseek.com/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "deepseek-v4-pro"
TEAM_MODEL_NAME = os.getenv("TEAM_MODEL_NAME") or "deepseek-flash"
AUTO_APPROVE = False

llm_local = ChatOpenAI(
    base_url=LOCAL_BASE_URL,
    api_key="not-needed",
    model=LOCAL_MODEL_NAME,
    temperature=0.7,
)

llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.7,
    streaming=False,
)

team_llm = ChatOpenAI(
    model=TEAM_MODEL_NAME,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.5,
    streaming=False,
)
