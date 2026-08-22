import os
import time
import uuid
from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai

app = FastAPI()

# 讀取金鑰
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"status": "AI File Checker Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. 產生暫存檔名
    ext = file.filename.split(".")[-1]
    temp_path = f"{uuid.uuid4()}.{ext}"
    
    try:
        # 2. 儲存檔案
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # 3. 上傳給 Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai_file = genai.upload_file(path=temp_path)

        # 4. 如果是影片，等待分析完成
        if file.content_type.startswith("video"):
            while genai_file.state.name == "PROCESSING":
                time.sleep(2)
                genai_file = genai.get_file(genai_file.name)
        
        # 5. 指令
        prompt = "分析此檔案：1.摘要 2.內容事實查核 3.AI生成痕跡分析 4.信任分數(0-100)。請用繁體中文回答。"
        response = model.generate_content([genai_file, prompt])
        
        os.remove(temp_path)
        return {"report": response.text}

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return {"report": f"伺服器出錯: {str(e)}"}
