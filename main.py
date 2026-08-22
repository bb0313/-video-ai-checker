import os
import time
import uuid
from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai

app = FastAPI()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"status": "AI File Checker Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. 取得檔案副檔名與 MIME 類型
    content_type = file.content_type  # 例如: image/jpeg 或 video/mp4
    ext = file.filename.split(".")[-1] if "." in file.filename else "tmp"
    temp_path = f"{uuid.uuid4()}.{ext}"
    
    try:
        # 2. 儲存檔案
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # 3. 上傳給 Gemini (修正點：明確指定 mime_type)
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai_file = genai.upload_file(path=temp_path, mime_type=content_type)

        # 4. 如果是影片，等待處理
        if content_type.startswith("video"):
            while genai_file.state.name == "PROCESSING":
                time.sleep(2)
                genai_file = genai.get_file(genai_file.name)
        
        # 5. 讓 AI 分析
        prompt = "分析此檔案：1.摘要 2.事實查核 3.AI生成痕跡 4.信任分數(0-100)。用繁體中文回答。"
        response = model.generate_content([genai_file, prompt])
        
        os.remove(temp_path)
        return {"report": response.text}

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return {"report": f"伺服器出錯: {str(e)}"}
