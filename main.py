import os
import time
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
import google.generativeai as genai

app = FastAPI()

# 從環境變數讀取 API Key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"status": "AI Checker Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. 產生暫存路徑
    file_ext = file.filename.split(".")[-1]
    temp_path = f"{uuid.uuid4()}.{file_ext}"
    
    try:
        # 2. 儲存上傳的檔案
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # 3. 上傳到 Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        genai_file = genai.upload_file(path=temp_path)

        # 4. 如果是影片，需要等待處理
        if file.content_type.startswith("video"):
            while genai_file.state.name == "PROCESSING":
                time.sleep(2)
                genai_file = genai.get_file(genai_file.name)
        
        # 5. 讓 AI 分析內容
        prompt = """
        你是一個專業的影音真偽鑑定專家。請分析這份檔案並回答：
        1. 內容摘要：這是什麼內容？
        2. 事實查核：內容中提到的資訊是否屬實？
        3. AI 偵測：是否有 AI 生成痕跡（如手指不自然、背景閃爍、皮膚過於平滑）？
        4. 總結：信任分數 (0-100)。
        請用繁體中文詳細回答。
        """
        response = model.generate_content([genai_file, prompt])
        
        # 6. 清理暫存檔
        os.remove(temp_path)
        return {"report": response.text}

    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return {"report": f"伺服器錯誤: {str(e)}"}
