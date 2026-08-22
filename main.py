import os
import time
import uuid
from fastapi import FastAPI, Form
import google.generativeai as genai
import yt_dlp

app = FastAPI()

# 確保從 Render 環境變數抓取金鑰
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

def get_best_model():
    """自動偵測目前可用的模型"""
    try:
        # 列出所有可用的模型
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順序：1.5-flash -> 3.6-flash -> 1.5-pro -> 第一個可用的
        for target in ['models/gemini-1.5-flash', 'models/gemini-3.6-flash', 'models/gemini-1.5-pro']:
            if target in models:
                return target
        return models[0] if models else "gemini-1.5-flash"
    except:
        return "gemini-1.5-flash" # 保底方案

@app.get("/")
def home():
    return {"status": "AI Checker Online", "using_model": get_best_model()}

@app.post("/check")
async def check_video(video_url: str = Form(...)):
    filename = f"video_{uuid.uuid4()}.mp4"
    try:
        # 1. 下載影片
        ydl_opts = {
            'format': 'best',
            'outtmpl': filename,
            'quiet': True,
            'nocheckcertificate': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # 2. 自動偵測模型並分析
        target_model = get_best_model()
        print(f"Using model: {target_model}")
        
        model = genai.GenerativeModel(target_model)
        video_file = genai.upload_file(path=filename)
        
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
            
        prompt = "分析這段影片：1.事實查核 2.AI生成痕跡偵測 3.信任分數。請用繁體中文回答。"
        response = model.generate_content([video_file, prompt])
        
        if os.path.exists(filename):
            os.remove(filename)
            
        return {"report": response.text}
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)
        return {"report": f"發生錯誤: {str(e)}"}
