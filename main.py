import os
import time
import threading
from datetime import datetime, timedelta
import pygame
import pandas as pd
import requests
from dotenv import load_dotenv
import tkinter as tk
from tkinter import scrolledtext, messagebox
import random
import math

# Загружаем API-ключи из файла .env
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not GEMINI_API_KEY or not GOOGLE_API_KEY:
    raise ValueError("Один или оба API-ключа не найдены! Проверьте файл .env.")

# Функция для отправки данных на Gemini API (оставлена пустой для текущей задачи)
def send_data_to_gemini(data):
    pass

# Генерируем случайное количество остановок от 3 до 8
num_stops = random.randint(3, 8)

# Создаем DataFrame со случайным временем между остановками (в диапазоне от 5 до 20 секунд)
data = {'bus_stop': [str(i + 1) for i in range(num_stops)],
        'travel_time': [random.randint(5, 20) for _ in range(num_stops)]}
average_travel_times = pd.DataFrame(data).set_index('bus_stop')['travel_time']

# Убеждаемся, что bus_stops упорядочены
bus_stops = average_travel_times.index.tolist()

# Создаем прогноз прибытия на основе среднего времени
start_date = datetime.now()
forecast_entries = []
cumulative_time = 0
for bus_stop in bus_stops:
    avg_time = average_travel_times[bus_stop]
    cumulative_time += avg_time
    next_arrival = start_date + timedelta(seconds=int(cumulative_time))
    forecast_entries.append({
        'Time': next_arrival,
        'Bus Stop': bus_stop,
        'Forecasted Travel Time': avg_time
    })

forecast_df = pd.DataFrame(forecast_entries).set_index('Time')

# Функция для отображения информации об остановке
def show_stop_info(stop, time_remaining):
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно Tkinter
    messagebox.showinfo("Информация об остановке", f"Остановка: {stop}\nОсталось до прибытия: {time_remaining} секунд")
    root.destroy()

# Функция для отображения текста в отдельном окне
def show_text_in_window():
    window = tk.Tk()
    window.title("Прогноз прибытия автобуса")
    window.geometry("400x600")

    text_area = scrolledtext.ScrolledText(window, width=50, height=35)
    text_area.grid(column=0, row=0, padx=10, pady=10)

    # Отображение прогноза прибытия
    text_area.insert(tk.END, "Прогноз прибытия автобуса:\n\n")
    for index, row in forecast_df.iterrows():
        text_area.insert(tk.END, f"Время: {index.strftime('%H:%M:%S')}\n")
        text_area.insert(tk.END, f"Остановка: {row['Bus Stop']}\n")
        text_area.insert(tk.END, f"Прогнозируемое время в пути: {row['Forecasted Travel Time']:.2f} сек\n\n")

    window.mainloop()

# Создание графического интерфейса с помощью Pygame
def show_data_in_pygame():
    # Инициализация Pygame
    pygame.init()

    # Установка размера окна 1280x920
    screen_width = 1280
    screen_height = 920
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Визуализация маршрута автобуса")

    # Определение цветов
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREY = (169, 169, 169)
    DARK_GREEN = (34, 139, 34)

    # Загрузка и увеличение изображений
    bus_image = pygame.image.load('bus.png')
    bus_image = pygame.transform.scale(bus_image, (80, 40))
    stop_image = pygame.image.load('bus_stop.png')
    stop_image = pygame.transform.scale(stop_image, (40, 40))

    # Генерация координат для формы треугольника, квадрата или пятиугольника
    base_x, base_y = screen_width // 2, screen_height // 3
    stop_positions = {}
    if num_stops == 3:
        # Треугольная форма
        stop_positions = {
            bus_stops[0]: (base_x, base_y),
            bus_stops[1]: (base_x + 200, base_y + 300),
            bus_stops[2]: (base_x - 200, base_y + 300)
        }
    elif num_stops in [4, 5]:
        # Квадратная форма с дополнительной остановкой в центре, если 5 остановок
        stop_positions = {
            bus_stops[0]: (base_x - 200, base_y),
            bus_stops[1]: (base_x + 200, base_y),
            bus_stops[2]: (base_x + 200, base_y + 300),
            bus_stops[3]: (base_x - 200, base_y + 300)
        }
        if num_stops == 5:
            stop_positions[bus_stops[4]] = (base_x, base_y + 150)
    elif num_stops in [6, 7, 8]:
        # Пятиугольная форма (если 6-8, добавляем дополнительные остановки по окружности)
        radius = 300
        angle_increment = 360 / num_stops
        for i, stop in enumerate(bus_stops):
            angle = angle_increment * i
            x = base_x + radius * math.cos(math.radians(angle))
            y = base_y + radius * math.sin(math.radians(angle))
            stop_positions[stop] = (int(x), int(y))

    # Создаем список сегментов между остановками с учетом времени
    route_segments = []
    cumulative_times = [0]
    total_time = 0

    for i in range(len(bus_stops)):
        current_stop = bus_stops[i]
        next_stop = bus_stops[(i + 1) % len(bus_stops)]
        travel_time = average_travel_times[next_stop]
        total_time += travel_time
        cumulative_times.append(total_time)

        segment = {
            'start_stop': current_stop,
            'end_stop': next_stop,
            'travel_time': travel_time
        }
        route_segments.append(segment)

    # Время начала
    start_time = pygame.time.get_ticks()

    # Шрифт
    font = pygame.font.SysFont('Arial', 18)

    # Главный цикл
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Проверка нажатия на остановку
                mouse_pos = pygame.mouse.get_pos()
                for stop, pos in stop_positions.items():
                    stop_rect = pygame.Rect(pos[0] - 20, pos[1] - 20, 40, 40)
                    if stop_rect.collidepoint(mouse_pos):
                        # Рассчитываем время до прибытия на остановку
                        stop_index = bus_stops.index(stop)
                        current_time_sec = (pygame.time.get_ticks() - start_time) / 1000
                        time_remaining = cumulative_times[stop_index] - current_time_sec
                        time_remaining = max(0, int(time_remaining))  # Убираем отрицательные значения
                        show_stop_info(stop, time_remaining)

        # Очистка экрана
        screen.fill(DARK_GREEN)

        # Рисуем дороги (линии между остановками)
        for segment in route_segments:
            start_pos = stop_positions[segment['start_stop']]
            end_pos = stop_positions[segment['end_stop']]
            pygame.draw.line(screen, GREY, start_pos, end_pos, 5)

        # Рисуем остановки
        for stop, pos in stop_positions.items():
            screen.blit(stop_image, (pos[0] - stop_image.get_width() // 2, pos[1] - stop_image.get_height() // 2))
            text = font.render(f'{stop}', True, BLACK)
            screen.blit(text, (pos[0] - text.get_width() // 2, pos[1] + 20))

        # Обновляем позицию автобуса
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000

        # Определяем текущий сегмент
        if elapsed_time >= cumulative_times[-1]:
            segment_index = len(route_segments) - 1
            t = 1
        else:
            for i in range(len(cumulative_times) - 1):
                if cumulative_times[i] <= elapsed_time < cumulative_times[i + 1]:
                    segment_index = i
                    break
            t = (elapsed_time - cumulative_times[segment_index]) / (cumulative_times[segment_index + 1] - cumulative_times[segment_index])

        # Получаем позиции начала и конца текущего сегмента
        segment = route_segments[segment_index]
        start_pos = pygame.math.Vector2(stop_positions[segment['start_stop']])
        end_pos = pygame.math.Vector2(stop_positions[segment['end_stop']])

        # Интерполируем позицию автобуса
        bus_pos = start_pos.lerp(end_pos, t)

        # Рисуем автобус без изменения его ориентации
        bus_rect = bus_image.get_rect(center=(bus_pos.x, bus_pos.y))
        screen.blit(bus_image, bus_rect)

        # Обновляем дисплей
        pygame.display.flip()

        # Ограничиваем частоту кадров
        clock.tick(60)

    pygame.quit()

# Запускаем функцию отображения текста в отдельном потоке
text_thread = threading.Thread(target=show_text_in_window)
text_thread.start()

# Вызов функции для отображения окна Pygame
show_data_in_pygame()

# Дожидаемся закрытия окна с текстом
text_thread.join()
