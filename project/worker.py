import os
import time
import logging
import grpc
from celery import Celery
import os
import json
import requests
from pprint import pprint
import struct
celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


# Task that sends audio data to whisper server
@celery.task(name="recognize")
def recognize(audio):
    myobj = {'audio_data': audio}
    response = requests.post('localhost:8008', json=myobj)
    response = response.json()['prediction']
    return {'text': response}


#Task to own TTS server
@celery.task(name="synthesize")
def synthesize(text: str):
    tts_data = {
        'text': text,
        'speaker': 'name-of-voice-actor'
    }

    tts_headers = {
        'Authorization': 'auth-token',
        'Content-Type': 'application/json'
    }
    url = 'http://localhost:7500/api/v2/synthesize' # different url that I cant show
    tts_res = requests.post(url, headers=tts_headers, data=json.dumps(tts_data))
    try:
        tts_res.raise_for_status()
        tts_res = tts_res.content
    except requests.HTTPError:
        module = e.__class__.__module__
        if module is None or module == str.__class__.__module__:
            errmsg = e.__class__.__name__
        errmsg = module + '.' + e.__class__.__name__

        logging.error("TTS error: %s >> %s", errmsg, str(e))

        tts_res = "Извините, проводятся технические работы 🛠"

    return {'bytes': tts_res}
