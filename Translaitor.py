import threading
import time
import json
import os
import sys

# Импорты для распознавания речи, TTS, перевода и воспроизведения
from vosk import Model, KaldiRecognizer
import pyaudio
from gtts import gTTS
import pygame
from translate import Translator

# Глобальные переменные для обмена данными
input_device_name = None
output_device_name = None

removes_fiels = []

# Потоки и управление ими
recognition_thread = None
recognition_running = threading.Event()

# Инициализация TTS
pygame.mixer.init()

# Модель Vosk
MODEL_PATH = "small_model"

# Проверка модели
if not os.path.exists(MODEL_PATH):
    print(f"Ошибка: Модель Vosk не найдена в {MODEL_PATH}. Загрузите модель.")
    sys.exit(1)

model = Model(MODEL_PATH)

def recognize_speech():
    """Функция для распознавания речи и перевода"""
    global recognition_running
    p = pyaudio.PyAudio()
    stream = None
    recognizer = None
    try:
        # Поиск устройства по имени (можно улучшить)
        device_index = None
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if input_device_name and input_device_name in info['name']:
                device_index = i
                break
        if device_index is None:
            print("Входное устройство не найдено. Используем дефолтное.")
            device_index = None

        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=16000,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=8000)
        recognizer = KaldiRecognizer(model, 16000)

        while recognition_running.is_set():
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    print(f"Распознанный текст: {text}")
                    # Перевод
                    translated = translate_text(text)
                    print(f"Перевод: {translated}")
                    # Озвучивание
                    tts(translated)
            time.sleep(0.1)
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

def tts(text):
    """Функция озвучивания текста"""
    try:
        filename = f"tts_output_{int(time.time())}.mp3"
        tts_obj = gTTS(text=text, lang='en', slow=False)
        tts_obj.save(filename)
        removes_fiels.append(os.path.join(os.path.dirname(__file__), filename))

        # Воспроизведение
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        # os.remove(os.path.join(os.path.dirname(__file__), filename))


    except Exception as e:
        print(f"Ошибка TTS: {e}")

def translate_text(text):
    """Перевод текста с русского на английский"""
    try:
        translator = Translator(from_lang='ru', to_lang='en')
        return translator.translate(text)
    except Exception as e:
        print(f"Ошибка перевода: {e}")
        return text

def start(output_device, input_device):
    """Запуск распознавания и перевода"""
    global recognition_thread
    global recognition_running
    input_device_name = input_device
    output_device_name = output_device

    if recognition_thread and recognition_thread.is_alive():
        print("Уже запущено")
        return

    recognition_running.set()
    recognition_thread = threading.Thread(target=recognize_speech)
    recognition_thread.start()
    print("Распознавание запущено.")

def removes_files():
    if removes_fiels:
        for f in range(removes_fiels):
            os.remove(removes_fiels[f])


def exit_translate():
    """Остановка распознавания"""
    global recognition_running

    # delete = threading.Thread(target=removes_files)
    # delete.start()
    # delete.join()

    recognition_running.clear()
    if recognition_thread:
        recognition_thread.join()
        print("Распознавание остановлено.")
