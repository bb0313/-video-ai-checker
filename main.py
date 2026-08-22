import os
import time
import uuid
from fastapi import FastAPI, File, UploadFile
from google.oauth2 import service_account
from google.genai import client
from google.genai import types

app = FastAPI()

# 1. 載入 Service Account JSON 金鑰
credentials = service_account.Credentials.from_service_account_file(
    'service_account.json'
)

# 2. 初始化 Vertex AI Client
ai_client = client.Client(
    vertexai=True,
    project="zhenapp-451200",  # ⚠️ 請替換為你的 GCP 專案 ID (例如 zhenAPP 的實際 ID)
    location="us-central1",
    credentials=credentials
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content_type = file.content_type
    ext = file.filename.split(".")[-1] if "." in file.filename else "tmp"
    temp_path = f"{uuid.uuid4()}.{ext}"

    try:
        # 儲存暫存檔
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # 使用 SDK 上傳檔案至 Vertex AI Media Storage
        uploaded_file = ai_client.files.upload(
            file=temp_path,
            config=types.UploadFileConfig(mime_type=content_type)
        )

        # 影片處理等待
        if content_type.startswith("video"):
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = ai_client.files.get(name=uploaded_file.name)

        # 呼叫 Gemini 進行分析
        prompt = "分析此檔案：1.摘要 2.事實查核 3.AI生成痕跡 4.信任分數(0-100)。用繁體中文回答。"
        
        response = ai_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[uploaded_file, prompt]
        )

        # 刪除本地暫存
        if os.path.exists(temp_path):
            os.remove(temp_path)

        return {"report": response.text}

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"report": f"伺服器出錯: {str(e)}"}
