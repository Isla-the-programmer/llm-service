from celery.result import AsyncResult
from fastapi import Body, FastAPI, Form, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import base64
import grpc
from speech_kz_api.speech_kz_api_pb2_grpc import SpeechKzApiStub
from speech_kz_api.speech_kz_api_pb2 import AudioEncoding, StreamingRecognizeRequest, StreamingRecognitionConfig, \
    RecognitionConfig, RecognizeRequest
import logging
import time
import base64
from pydantic import BaseModel
from typing import Optional

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_json(self, websocket: WebSocket, json_object: dict):
        await websocket.send_json(json_object)

manager = ConnectionManager()

class AudioData(BaseModel):
    format: str
    audio: str

class CallRequest(BaseModel):
    callID: str
    audio: AudioData

app = FastAPI()

@app.get("/")
async def home(request: Request):
    return {'message': 'server is on'}


@app.websocket("/ai/bot/{client_id}", status_code=201)
async def run_task(websocket: WebSocket):
    from worker import recognize, synthesize
    await manager.connect(websocket)
    try:
        while True:
            audio = await websocket.receive()
            task = recognize.delay(audio)
            time.sleep(0.5)
            task_result = AsyncResult(task.id)
            task_result = task_result.result['text']['results'][0]['alternatives'][0]['transcript']
            task = synthesize.delay('Извините, я вас не понимаю.')
            time.sleep(1)
            task_result_audio = AsyncResult(task.id)
            task_result_audio = base64.b64encode(task_result_audio.result['bytes']).decode()
            response = {
                "data": {
                    #"callID": call_id,
                    "audio": {
                        "format": "wav",
                        "audio": task_result_audio
                    },
                    "command": {
                        "name": "play_audio",
                        "data": "string"
                    }
                }
            }
            manager.send_json(websocket, response)
            #return JSONResponse(response)
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

#@app.post("/audio")
#async def audio_asr():

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
