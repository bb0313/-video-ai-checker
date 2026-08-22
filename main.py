import os
import time
import uuid
from fastapi import FastAPI, Form
import google.generativeai as genai
import yt_dlp

app = FastAPI()

# 雲端安全設定：從環境變數讀取 KEY
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

@app.get("/")
def home():
    return {"status": "AI Checker is Online"}

@app.post("/check")
async def check_video(video_url: str = Form(...)):
    # 產生隨機檔名
    filename = f"video_{uuid.uuid4()}.mp4"
    try:
        # 1. 下載影片
        ydl_opts = {'format': 'best', 'outtmpl': filename, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 2. AI 分析
        model = genai.GenerativeModel('gemini-1.5-flash')
        video_file = genai.upload_file(path=filename)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        prompt = "分析這段影片：1.事實查核 2.AI生成痕跡偵測 3.信任分數。請用繁體中文回答。"
        response = model.generate_content([video_file, prompt])
        
        # 3. 清理檔案
        if os.path.exists(filename):
            os.remove(filename)
            
        return {"report": response.text}
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)
        return {"report": f"發生錯誤: {str(e)}"}
