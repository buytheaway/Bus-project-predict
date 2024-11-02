import os
import time
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import scrolledtext, messagebox

import matplotlib.pyplot as plt
import pandas as pd
import requests
from dotenv import load_dotenv

# Загружаем API-ключи из файла .env
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GEMINI_API_KEY or not GOOGLE_API_KEY:
    raise ValueError("Один или оба API-ключа не найдены! Проверьте файл .env.")


# Функция для отправки данных на Gemini API с ограничением одного запроса в минуту
def send_data_to_gemini(data):
    url = "https://api.gemini.com/v1/order/new"
    headers = {"X-GEMINI-APIKEY": GEMINI_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=data)
    time.sleep(60)  # Ожидаем 60 секунд, чтобы не превышать лимит

    if response.status_code == 200:
        print("Данные успешно отправлены на Gemini:", response.json())
    else:
        print("Ошибка отправки данных на Gemini:", response.status_code, response.text)


# Загрузка и обработка данных из датасетов
# Загрузка данных из новых датасетов
dataset_1 = pd.read_csv(r'C:\Users\mukha\Documents\GitHub\Hakaton-cts\Датасет #1')
dataset_2 = pd.read_csv(r'C:\Users\mukha\Documents\GitHub\Hakaton-cts\Датасет 2')
dataset_3 = pd.read_csv(r'C:\Users\mukha\Documents\GitHub\Hakaton-cts\Датасет 3')
dataset_4 = pd.read_csv(r'C:\Users\mukha\Documents\GitHub\Hakaton-cts\Датасет 4')

# Преобразуем время прибытия и отправления в datetime и вычисляем travel_time
dataset_1['arrival_time'] = pd.to_datetime(dataset_1['arrival_time'], format='%H:%M:%S')
dataset_1['departure_time'] = pd.to_datetime(dataset_1['departure_time'], format='%H:%M:%S')
dataset_1['travel_time'] = (dataset_1['departure_time'] - dataset_1['arrival_time']).dt.total_seconds()

# Преобразование для сопоставления bus_stop и stop_id
dataset_1['bus_stop'] = dataset_1['bus_stop'].astype(str)
dataset_2['stop_id'] = dataset_2['stop_id'].astype(str)
dataset_1 = dataset_1.merge(dataset_2, how='left', left_on='bus_stop', right_on='stop_id')

# Рассчитываем среднее время прибытия для каждой остановки
average_travel_times = dataset_1.groupby('bus_stop')['travel_time'].mean()

# Прогноз прибытия на следующую остановку
start_date = datetime.now()

# Создаем прогноз на основе среднего времени для каждой остановки
forecast_entries = []
for bus_stop, avg_time in average_travel_times.items():
    next_arrival = start_date + timedelta(seconds=avg_time)
    forecast_entries.append({
        'Time': next_arrival,
        'Bus Stop': bus_stop,
        'Forecasted Travel Time': avg_time
    })

forecast_df = pd.DataFrame(forecast_entries).set_index('Time')


# Создание графического интерфейса
def show_data_in_window():
    # Создаем основное окно
    window = tk.Tk()
    window.title("Прогноз прибытия автобуса")
    window.geometry("600x400")

    # Текстовое поле для вывода данных
    text_area = scrolledtext.ScrolledText(window, width=70, height=20)
    text_area.grid(column=0, row=0, padx=10, pady=10)

    # Отображение среднего времени прибытия
    text_area.insert(tk.END, "Среднее время прибытия по каждой остановке:\n")
    for bus_stop, avg_time in average_travel_times.items():
        text_area.insert(tk.END, f"Остановка {bus_stop}: {avg_time:.2f} секунд\n")

    # Отображение прогноза прибытия
    text_area.insert(tk.END, "\nПрогноз прибытия следующего автобуса:\n")
    for index, row in forecast_df.iterrows():
        text_area.insert(tk.END,
                         f"{index}: Остановка {row['Bus Stop']}, Прогноз {row['Forecasted Travel Time']:.2f} секунд\n")

    # Функция для отправки прогноза на Gemini API
    def send_forecast_to_gemini():
        for _, entry in forecast_df.reset_index().iterrows():
            gemini_entry = {
                "Time": entry['Time'].isoformat(),
                "Bus Stop": entry['Bus Stop'],
                "Forecasted Travel Time": entry['Forecasted Travel Time']
            }
            send_data_to_gemini(gemini_entry)

    # Запуск основного цикла Tkinter
    window.mainloop()


# Вызов функции для отображения окна
show_data_in_window()