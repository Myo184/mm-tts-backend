import os
import re
import json
import edge_tts
import base64
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import Response

app = FastAPI()

# CORS စနစ် လုံးဝ လွတ်လပ်စွာ ခွင့်ပြုခြင်း
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str
    rate: str
    pitch: str

def split_text_to_sentences(text):
    # မြန်မာစာ ဝါကျအဆုံးသတ်သင်္ကေတများ (။ ၊ သို့မဟုတ် စာကြောင်းအသစ်) ဖြင့် စာကြောင်းခွဲခြင်း
    raw_sentences = re.split(r'([။၊\n])', text)
    sentences = []
    current = ""
    for part in raw_sentences:
        if part in ["။", "၊", "\n"]:
            if current.strip():
                sentences.append(current.strip() + (part if part != "\n" else ""))
            current = ""
        else:
            current += part
    if current.strip():
        sentences.append(current.strip())
    return [s for s in sentences if s.strip()]

@app.post("/api/tts")
async def text_to_speech(data: TTSRequest):
    try:
        # အမျိုးသားသံ (သီဟ) နှင့် အမျိုးသမီးသံ (နဒီ) ခွဲခြားခြင်း
        voice_name = "my-MM-ThihaNeural" if data.voice == "th" else "my-MM-NadiNeural"
        
        # Rate နှင့် Pitch parameter ပုံစံများကို သန့်စင်ခြင်း
        rate_param = data.rate if ('+' in data.rate or '-' in data.rate) else f"+{data.rate}"
        pitch_param = data.pitch if ('+' in data.pitch or '-' in data.pitch) else f"+{data.pitch}"

        communicate = edge_tts.Communicate(
            text=data.text, 
            voice=voice_name,
            rate=rate_param,
            pitch=pitch_param
        )
        
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]

        if not audio_data:
            error_payload = json.dumps({"success": False, "detail": "Audio generation failed."}, ensure_ascii=False).encode('utf-8')
            return Response(content=error_payload, media_type="application/json; charset=utf-8")

        # အသံဖိုင်ကို Base64 ပြောင်းလဲခြင်း
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        audio_url = f"data:audio/mp3;base64,{audio_base64}"

        # --- SRT အချိန်မှတ်များ စနစ်တကျ တွက်ချက်တည်ဆောက်ခြင်း ---
        sentences = split_text_to_sentences(data.text)
        if not sentences:
            sentences = [data.text]

        srt_lines = []
        total_chars = sum(len(s) for s in sentences)
        
        try:
            speed_val = int(data.rate.replace('%', '').replace('+', ''))
        except:
            speed_val = 0
            
        # အမြန်နှုန်းအလိုက် စုစုပေါင်းကြာချိန်ကို အချိုးကျ ညှိယူခြင်း
        speed_factor = 1 - (speed_val / 150)
        total_duration = max(5, round(total_chars * 0.28 * speed_factor))
        time_per_char = total_duration / total_chars if total_chars > 0 else 0.28

        current_time = 0.0
        for i, sentence in enumerate(sentences, 1):
            sent_len = len(sentence)
            duration = max(2.5, sent_len * time_per_char)
            
            start_sec = current_time
            end_sec = current_time + duration
            
            def format_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds - int(seconds)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            srt_lines.append(f"{i}")
            srt_lines.append(f"{format_time(start_sec)} --> {format_time(end_sec)}")
            srt_lines.append(f"{sentence}")
            srt_lines.append("")
            
            current_time = end_sec

        srt_content = "\r\n".join(srt_lines)

        # ⭐️ ဤနေရာတွင် ဒေတာများကို JSON string ပြောင်းပြီး သေချာပေါက် .encode('utf-8') လုပ်၍ byte အဖြစ် ပို့ဆောင်ခြင်းဖြစ်သည်
        response_dict = {
            "success": True,
            "audioUrl": audio_url,
            "srtData": srt_content
        }
        
        response_bytes = json.dumps(response_dict, ensure_ascii=False).encode('utf-8')

        return Response(content=response_bytes, media_type="application/json; charset=utf-8")

    except Exception as e:
        err_dict = {"success": False, "detail": str(e)}
        err_bytes = json.dumps(err_dict, ensure_ascii=False).encode('utf-8')
        return Response(content=err_bytes, media_type="application/json; charset=utf-8", status_code=500)
