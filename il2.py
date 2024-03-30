#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import time
import sys
import os
import os.path
import json
import subprocess
import wave
import pyaudio

import speech_recognition as sr
from google.cloud import texttospeech
#from pydub import AudioSegment

import keyboard2 as kb


# Instantiates a client
client = texttospeech.TextToSpeechClient(
    client_options={"api_key": open("credentials").read().strip()}
)
#translate_client = translate.TranslationServiceClient()

def get_voiceline(output, text, language_code, model, gender_name):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    if gender_name == "male":
        gender = texttospeech.SsmlVoiceGender.MALE
    else:
        gender = texttospeech.SsmlVoiceGender.FEMALE
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code, name=model, ssml_gender=gender,
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(output, "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print(f"Audio content written to file {output}")


COMMANDS = [
    ("gunners engage at long range", [kb.VK_RMENU, kb.VK_NINE], "gunners copy"),
    ("gunners fire at will", [kb.VK_RMENU, kb.VK_ONE], "gunners copy"),
    ("lower landing gear", [kb.VK_LCONTROL, kb.VK_G], "gear copy"),
    ("raise landing gear", [kb.VK_LMENU, kb.VK_G], "gear copy"),
    ("eject eject eject", [kb.VK_LCONTROL, kb.VK_E], "ejecting"),
    ("deploy spoilers", [kb.VK_RMENU, kb.VK_B], "spoilers copy"),
    ("retract spoilers", [kb.VK_RCONTROL, kb.VK_B], "spoilers copy"),
    ("feather engine one", [kb.VK_LCONTROL, kb.VK_F], "engine copy"),
    ("feather engine two", [kb.VK_LCONTROL, kb.VK_LMENU, kb.VK_F], "engine copy"),
    ("open bomb doors", [kb.VK_LCONTROL, kb.VK_N], "bombs copy"),
    ("close bomb doors", [kb.VK_LMENU, kb.VK_N], "bombs copy"),
    ("squadron attack nearest air target", [kb.VK_LMENU, kb.VK_ONE], "squadron copy"),
    ("squadron attack nearest ground target", [kb.VK_LMENU, kb.VK_TWO], "squadron copy"),
    ("squadron patrol for ground targets", [kb.VK_LMENU, kb.VK_EIGHT], "squadron copy"),
    ("squadron formation", [kb.VK_LCONTROL, kb.VK_NINE], "squadron copy"),
    ("squadron return to base", [kb.VK_LMENU, kb.VK_ZERO], "squadron copy"),
    ("toggle engine one", [kb.VK_RCONTROL, kb.VK_ONE], "engine copy"),
    ("toggle engine two", [kb.VK_RCONTROL, kb.VK_TWO], "engine copy"),
]


# Make sure we have all voicelines
voicelines = set()
for (_, _, voiceline) in COMMANDS + [(None, None, "say again")]:
    if not os.path.exists(f"./voicelines/{voiceline}.wav"):
        voicelines.add(voiceline)

for voiceline in voicelines:
    get_voiceline(f"voicelines/{voiceline}.wav", voiceline, "en-US", "en-US-Neural2-H", "female")

voicelines = {}
for (_, _, voiceline) in COMMANDS + [(None, None, "say again")]:
    voicelines[voiceline] = wave.open(f"voicelines/{voiceline}.wav")

print(voicelines["gear copy"].getsampwidth())

phrases = []
for (phrase, _, _) in COMMANDS:
    phrases.append(phrase)

pa = pyaudio.PyAudio()
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    print(info["name"])
    if info["name"] == "Speakers (4- HTC Vive)":
        stream = pa.open(output_device_index = i, format =
                    pa.get_format_from_width(2),
                    channels = 1,
                    rate = 24000,
                    output = True)
        break
    #print(pa.get_device_info_by_index(i))

def play_voiceline(voiceline):
    chunk = 1024

    wf = wave.open(f"voicelines/{voiceline}.wav")

    # read data (based on the chunk size)
    data = wf.readframes(chunk)

    # play stream (looping from beginning of file to the end)
    while data:
        # writing to the stream is what *actually* plays the sound.
        stream.write(data)
        data = wf.readframes(chunk)


# this is called from the background thread
def callback(recognizer, audio):
    # received audio data, now we'll recognize it using Google Speech Recognition
    try:
        # Note: See https://github.com/Uberi/speech_recognition/issues/334 r.e. preferred_phrases
        heard = recognizer.recognize_google_cloud(audio, credentials_json="wows-uploader-a9094a00ef41.json", preferred_phrases=phrases)
        heard = heard.lower().strip()
        print(f"Got '{heard}'")
        got_command = False
        for (command, keys, response) in COMMANDS:
            if command == heard:
                #play_voiceline(voicelines[response])
                got_command = True
                for key in keys:
                    kb.PressKey(key)
                    time.sleep(0.05)
                for key in reversed(keys):
                    kb.ReleaseKey(key)
                    time.sleep(0.01)
                play_voiceline(response)
                break
        if not got_command:
            play_voiceline("say again")
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))


m = None
for i,name in enumerate(sr.Microphone.list_microphone_names()):
    print(i, name)
    if name == "Microphone (3- HTC Vive)":
        m = sr.Microphone(i)
        break


r = sr.Recognizer()
with m as source:
    r.adjust_for_ambient_noise(source)

# start listening in the background (note that we don't have to do this inside a `with` statement)
stop_listening = r.listen_in_background(m, callback)
# `stop_listening` is now a function that, when called, stops background listening

# do some more unrelated things
while True:
    time.sleep(0.1)  # we're not listening anymore, even though the background thread might still be running for a second or two while cleaning up and stopping
