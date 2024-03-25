import asyncio

import numpy as np
import uvicorn
from fastapi import Depends, FastAPI, Request
from faster_whisper import WhisperModel

from datetime import datetime 
import datetime as dt 

app = FastAPI()

NUM_WORKERS = 16
MODEL_TYPE = "large-v3"
LANGUAGE_CODE = "en"
CPU_THREADS = 18
VAD_FILTER = True


def create_whisper_model() -> WhisperModel:
    whisper = WhisperModel(MODEL_TYPE,
                           device="cuda",
                           compute_type="int8",
                           num_workers=NUM_WORKERS,
                           cpu_threads=18,
                           download_root="./models")
    print("Loaded model")
    return whisper


model = create_whisper_model()
print("Loaded model")


async def parse_body(request: Request):
    data: bytes = await request.body()
    return data


def execute_blocking_whisper_prediction(model: WhisperModel, audio_data_array) -> str:
    segments, _ = model.transcribe(audio_data_array,
                                   language=LANGUAGE_CODE,
                                   beam_size=5,
                                   vad_filter=VAD_FILTER,
                                   vad_parameters=dict(min_silence_duration_ms=1000))
    segments = [s.text for s in segments]
    transcription = " ".join(segments)
    transcription = transcription.strip()
    return transcription


@app.post("/predict")
async def predict(audio_data: bytes = Depends(parse_body)):
    # Convert the audio bytes to a NumPy array
    audio_data_array: np.ndarray = np.frombuffer(audio_data, np.int16).astype(np.float32) / 255.0

    try:
        # Run the prediction on the audio data
        result = await asyncio.get_running_loop().run_in_executor(None, execute_blocking_whisper_prediction, model,
                                                                  audio_data_array)

    except Exception as e:
        print(e)
        result = "Error"

    date_time = datetime.fromtimestamp(dt.datetime.now().timestamp())

    with open('/home/kdtadmin/turlykhan/whisper/logs.txt', 'a') as logs:
        logs.write(f"prediction: {result}, Time : {str(date_time)}\n")

    return {"prediction": result, "Time" : str(date_time)}


if __name__ == "__main__":
    # Run the FastAPI app with multiple threads
    uvicorn.run(app, host="0.0.0.0", port=8008)
