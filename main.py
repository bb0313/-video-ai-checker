import os
import time
import uuid
from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai

app = FastAPI()

# ⚠️ 只要這行就好，不要去讀取任何 .json 檔案
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"status": "AI Checker Online"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    temp_path = f"{uuid.uuid4()}.{ext}"
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        model = genai.GenerativeModel('gemini-3.6-flash')
        # 明確指定 mime_type
        genai_file = genai.upload_file(path=temp_path, mime_type=file.content_type)

        if file.content_type.startswith("video"):
            while genai_file.state.name == "PROCESSING":
                time.sleep(2)
                genai_file = genai.get_file(genai_file.name)
        
        prompt = "分析此檔案：1.摘要 2.事實查核 3.AI生成痕跡偵測 4.信任分數。用繁體中文回答。"
        response = model.generate_content([genai_file, prompt])
        
        os.remove(temp_path)
        return {"report": response.text}
    except Exception as e:
        if os.path.exists(temp_path): os.remove(temp_path)
        return {"report": f"伺服器錯誤: {str(e)}"}
