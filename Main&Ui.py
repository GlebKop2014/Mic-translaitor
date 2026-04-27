from PyQt6 import uic
from PyQt6.QtWidgets import QApplication
import pyaudio
import subprocess
import csv
import threading

# Загрузка интерфейса
Form, Window = uic.loadUiType("Main.ui")

def list_audio_input_devices_windows():
    """Получение списка микрофонов через PowerShell"""
    command = (
        'Get-PnpDevice -Class AudioEndpoint | '
        'Where-Object { $_.FriendlyName -match "Microphone" '
        '-or $_.FriendlyName -match "CABLE Input" '
        '-or $_.FriendlyName -match "Realtek\\(R\\) Audio" } | '
        'Select-Object -Property FriendlyName | '
        'ConvertTo-Csv -NoTypeInformation'
    )
    try:
        result = subprocess.run(
            ['powershell', '-Command', command],
            capture_output=True,
            text=False,
            check=True
        )
        if result.stdout:
            output = result.stdout.decode('utf-8', errors='ignore')
            devices = []
            for line in output.strip().splitlines()[1:]:
                reader = csv.reader([line])
                for row in reader:
                    if row:
                        devices.append(row[0])
            return devices
        else:
            print("Пустой вывод от команды PowerShell.")
            return []
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения команды: {e}")
        return []

def get_audio_devices():
    """Получение списка аудиоустройств через PyAudio"""
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            devices.append(device_info['name'])
    p.terminate()
    return devices

def fix_string(s):
    """Обработка строк для устранения искажений"""
    return s.encode('windows-1252', errors='ignore').decode('utf-8', errors='ignore')

def main():
    app = QApplication([])

    window = Window()
    form = Form()
    form.setupUi(window)

    # Добавим состояние как атрибут
    form.start = True

    def populate_devices():
        """Заполнение списков устройств"""
        devices = list_audio_input_devices_windows()
        devices = [fix_string(d) for d in devices]
        form.output_microphone.clear()
        form.input_microphone.clear()
        form.output_microphone.addItems(devices)
        form.input_microphone.addItems(devices)

    populate_devices()

    def start_code():
        """Обработка запуска"""
        input_dev = form.input_microphone.currentText()
        output_dev = form.output_microphone.currentText()
        print(f"Выбранный входной микрофон: {input_dev}")
        print(f"Выбранный выходной микрофон: {output_dev}")

        import Main
        Main.input = input_dev
        Main.out = output_dev

        # Запуск основной логики
        Main.start(output_dev, input_dev)

    def on_start_button_clicked():
        if form.start:
            # Запуск потока
            thread = threading.Thread(target=start_code)
            thread.start()
            form.Start_Button.setText("Stop")
            form.start = False
        else:
            # Остановка
            import Main
            Main.removes_fiels()
            Main.exit_translate()
            form.Start_Button.setText("Start")
            form.start = True

    form.Start_Button.clicked.connect(on_start_button_clicked)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()