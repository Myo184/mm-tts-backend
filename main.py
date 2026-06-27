import os
import edge_tts
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse

app = FastAPI()

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

@app.post("/api/tts")
async def text_to_speech(data: TTSRequest):
    try:
        voice_name = "my-MM-ThihaNeural" if data.voice == "th" else "my-MM-NadiNeural"
        communicate = edge_tts.Communicate(text=data.text, voice=voice_name)

        output_filename = "output.mp3"
        await communicate.save(output_filename)

        return FileResponse(output_filename, media_type="audio/mp3", filename="tts.mp3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
