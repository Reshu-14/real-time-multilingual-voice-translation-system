from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
from gtts import gTTS
import os
import time
from translate import Translator
import speech_recognition as sr
from threading import Lock

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Supported languages with proper codes
LANGUAGES = {
    'en': {'name': 'English', 'speech_code': 'en-US', 'flag': '🇬🇧'},
    'te': {'name': 'Telugu', 'speech_code': 'te-IN', 'flag': '🇮🇳'},
    'hi': {'name': 'Hindi', 'speech_code': 'hi-IN', 'flag': '🇮🇳'},
    'ta': {'name': 'Tamil', 'speech_code': 'ta-IN', 'flag': '🇮🇳'},
    'kn': {'name': 'Kannada', 'speech_code': 'kn-IN', 'flag': '🇮🇳'},
    'ml': {'name': 'Malayalam', 'speech_code': 'ml-IN', 'flag': '🇮🇳'}
}

recognizer = sr.Recognizer()
microphone = sr.Microphone()
thread_lock = Lock()

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/translator')
def translator():
    return render_template('translator.html', languages=LANGUAGES)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

def translate_text(text, src_lang, dest_lang):
    try:
        translator = Translator(from_lang=src_lang, to_lang=dest_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def text_to_speech(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        audio_file = f"static/output_{int(time.time())}.mp3"
        tts.save(audio_file)
        return f"/{audio_file}"
    except Exception as e:
        print(f"TTS error: {e}")
        return None

@socketio.on('send_message')
def handle_message(data):
    with thread_lock:
        text = data['text']
        src_lang = data['src_lang']
        dest_lang = data['dest_lang']
        room = data['room']
        
        # Translate the message
        translated = translate_text(text, src_lang, dest_lang)
        
        # Generate speech
        audio_file = text_to_speech(translated, dest_lang)
        
        # Broadcast to room
        socketio.emit('receive_message', {
            'original': text,
            'translated': translated,
            'audio_file': audio_file,
            'src_lang': src_lang,
            'dest_lang': dest_lang
        }, room=room)

@socketio.on('join')
def on_join(data):
    room = data['room']
    socketio.emit('system_message', {
        'text': f"User has joined conversation {room}",
        'type': 'info'
    }, room=room)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    socketio.emit('system_message', {
        'text': f"User has left conversation {room}",
        'type': 'info'
    }, room=room)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    socketio.run(app, debug=True, port=5000)