import Adafruit_DHT as DHT
import pigpio
import time
import math
import pandas as pd
import re, os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk
from tkinter import filedialog, ttk
from datetime import datetime, timedelta
import os
import threading
import schedule
from gpiozero import LED, Button

# コールバック関数
def count_pulses(gpio, level, tick):
    global pulse_count
    pulse_count += 1

def read_dht_sensor(sensor, pin):
    humidity, temperature = DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        return temperature, humidity
    else:
        return None, None

def calculate_water_temperature(pulse_count, time_diff):
    frequency = float(pulse_count) / time_diff
    thermistor_resistance = 69444.4 / (frequency + 1e-9) - 0.491  # [Kohm]
    water_temperature = 3380.0 / (9.04 + math.log(thermistor_resistance)) - 273.0  # [Celsius Degree]
    return water_temperature

def save_daily_data():
    current_date = datetime.now() - timedelta(days=1)
    filename = f"waterTemp_{current_date.strftime('%Y%m%d')}.csv"
    df = pd.DataFrame(data, columns=['Time', 'Temperature (C)', 'Humidity (%)', 'Water Temperature (C)'])
    df.to_csv(filename, index=False)
    print(f"Saved data to {filename}")

def save_data():
    if data:
        current_date = datetime.now().strftime('%Y%m%d')
        filename = f"waterTemp_{current_date}.csv"
        df = pd.DataFrame(data, columns=['Time', 'Temperature (C)', 'Humidity (%)', 'Water Temperature (C)'])
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
    else:
        print("No data to save")

def open_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        date_str = extract_date_from_filename(file_path)
        plot_csv_data(file_path, date_str)

def extract_date_from_filename(file_path):
    match = re.search(r'waterTemp_(\d{8})\.csv', file_path)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
    return None

def plot_csv_data(file_path, date_str):
    df = pd.read_csv(file_path)
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M')
    df['Time'] = df['Time'].dt.strftime('%H:%M')

    fig_csv = Figure(figsize=(6, 4), dpi=100)
    ax1_csv = fig_csv.add_subplot(111)
    ax2_csv = ax1_csv.twinx()

    ax1_csv.plot(df['Time'], df['Temperature (C)'], label='Temperature (C)', color='tab:blue')
    ax1_csv.plot(df['Time'], df['Water Temperature (C)'], label='Water Temperature (C)', color='tab:green')
    ax2_csv.plot(df['Time'], df['Humidity (%)'], label='Humidity (%)', color='tab:orange')

    ax1_csv.set_xlabel('Time (hh:mm)')
    ax1_csv.set_ylabel('Temperature (C)', color='tab:blue')
    ax2_csv.set_ylabel('Humidity (%)', color='tab:orange')

    ax1_csv.legend(loc='upper left')
    ax2_csv.legend(loc='upper right')

    num_labels = len(df['Time'])
    step = max(num_labels // 8, 1)
    ax1_csv.set_xticks(df['Time'][::step])

    for label in ax1_csv.get_xticklabels():
        label.set_rotation(45)

    ax1_csv.set_facecolor('white')

    plt.grid(True)

    new_window = tk.Toplevel(root)
    new_window.title(f"Data from {date_str}")

    canvas = FigureCanvasTkAgg(fig_csv, master=new_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1, pady=3)

def collect_data():
    global current_time, pulse_count, notFirstTime, water_temperature

    date_data = datetime.now().strftime('%H:%M')
    temperature, humidity = read_dht_sensor(SENSOR_TYPE, DHT_PIN)
    
    previous_time = current_time
    current_time = time.perf_counter_ns()
    time_difference = float(current_time - previous_time) * 1e-9

    if time_difference > 0 and notFirstTime:
        water_temperature = calculate_water_temperature(pulse_count, time_difference)
    else:
        water_temperature = None
        notFirstTime = True

    data.append([date_data, temperature, humidity, water_temperature])
    
    if len(data) > MAX_DATA_POINTS:
        data.pop(0)

    # 5分ごとにデータを収集する（300000ミリ秒 = 5分）
    root.after(300000, collect_data)

    # グラフの更新
    plot_data()
    
    # 最新の測定値をラベルに表示
    current_datetime = datetime.now()
    date_str = current_datetime.strftime('%Y-%m-%d %A')
    temp_str = f"Temperature: {temperature:.1f}°C" if temperature is not None else "Temperature: N/A"
    hum_str = f"Humidity: {humidity:.1f}%" if humidity is not None else "Humidity: N/A"
    water_temp_str = f"Water Temperature: {water_temperature:.1f}°C" if water_temperature is not None else "Water Temperature: N/A"

    date_label.config(text=date_str)
    temp_label.config(text=temp_str)
    hum_label.config(text=hum_str)
    water_temp_label.config(text=water_temp_str)

    pulse_count = 0

# 毎回データを保存
    if current_datetime.hour == 0 and current_datetime.minute <= 5:
        save_daily_data()

def plot_data():
    x_data = [row[0] for row in data]
    temp_data = [row[1] for row in data]
    hum_data = [row[2] for row in data]
    water_temp_data = [row[3] for row in data]
    
    # meajuring time more than 12 hours
    if len(x_data) >= (MAX_DATA_POINTS // 2):
        a = len(x_data) - MAX_DATA_POINTS // 2
        b = len(x_data)
    else:
        a = 0
        b = len(x_data)
    
    x_data_sub = x_data[a:]
    temp_sub = temp_data[a:]
    water_temp_sub = water_temp_data[a:]
    hum_sub = hum_data[a:]


    ax1.clear()
    ax2.clear()

    ax1.plot(x_data_sub, temp_sub, label='Temperature (C)', color='tab:blue')
    ax1.plot(x_data_sub, water_temp_sub, label='Water Temperature (C)', color='tab:green')
    ax2.plot(x_data_sub, hum_sub, label='Humidity (%)', color='tab:orange')

    ax1.set_xlabel('Time (hh:mm)')
    ax1.set_ylabel('Temperature (C)', color='tab:blue')
    ax2.set_ylabel('Humidity (%)', color='tab:orange')

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

    # x軸のラベルを30分おきに減らす
    num_labels = len(x_data_sub)
    step = max(num_labels // 9, 1)
    ax1.set_xticks(x_data_sub[::step])

    # x軸のラベルを回転
    for label in ax1.get_xticklabels():
        label.set_rotation(45)

    ax1.set_facecolor('white')

    for widget in plot_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

def on_closing():
    root.destroy()
    
def find_today_csv_files(directory):
    # 今日の日付を取得
    today = datetime.now().strftime('%Y%m%d')

    # ディレクトリ内の全ファイルをリスト
    files = os.listdir(directory)

    # 今日の日付を含むCSVファイルをフィルタリング
    today_files = [file for file in files if today in file and file.endswith('.csv')]

    return today_files

def checkTodayCsvFiles():
    # カレントディレクトリを指定
    current_directory = os.getcwd()

    # 今日の日付を含むCSVファイルを検索
    today_csv_files = find_today_csv_files(current_directory)

    if today_csv_files:
        print("Today's CSV files:", today_csv_files)
        df = pd.read_csv(today_csv_files[0])
        df['Time'] = pd.to_datetime(df['Time'], format='%H:%M')
        df['Time'] = df['Time'].dt.strftime('%H:%M')
#         print(df['Time'])

        a = len(df['Time'])
        b = max(a - MAX_DATA_POINTS, 0)

        for i in range(a-b):
            current_time = df['Time'][b+i]
            temperature, humidity = df['Temperature (C)'][b+i], df['Humidity (%)'][b+i]
            water_temperature = df['Water Temperature (C)'][b+i]

            data.append([current_time, temperature, humidity, water_temperature])

    else:
        print("No CSV files found for today.")

# LEDをオンにし、10秒後にオフにする関数
def turn_on_led():
    led.on()
    print(f"LED is ON at {datetime.now().strftime('%H:%M:%S')}")
    # 10秒後にLEDをオフにするタイマーを設定
    threading.Timer(10, turn_off_led).start()

# LEDをオフにする関数
def turn_off_led():
    led.off()
    print(f"LED is OFF at {datetime.now().strftime('%H:%M:%S')}")

def is_duringOnTime():
    global led_already_on
    # 現在の時刻を分に変換
    now = datetime.now()
    current_time = now.hour * 60 + now.minute

    print('in during time', current_time, 'led_already_on', led_already_on)
    if (8 * 60 - 5 <= current_time) and \
        (current_time <= 8 * 60 + 5):
        return True
    else:
        return False

# 時間をチェックし、前後5分以内ならLEDをオンにする関数
def check_and_turn_on_led():
    global led_on_time, led_already_on
    now = datetime.now()
    current_time = now.hour * 60 + now.minute  # 現在の時刻を分に変換
    print(f"current: {now.strftime('%H:%M:%S')}")
    if current_time - led_on_time > 10:
        led_already_on = False

    # 8:00および19:00の前後5分以内かチェック
    if led_control_enabled and is_duringOnTime()\
       and (not led_already_on):
        led_control_ON = True
        turn_on_led()
        led_already_on = True
        # 現在の時刻を分に変換
        now = datetime.now()
        led_on_time = now.hour * 60 + now.minute
    else:
        led_control_ON = False

# LEDオンオフの切り替えボタンの処理
def toggle_led_control():
    global led_control_enabled
    led_control_enabled = not led_control_enabled

    if led_control_enabled:
        # LED制御が可能な状態
        toggle_button.config(text="Running", bg="orange", activebackground="orange")
        test_mode_button.config(state=tk.DISABLED)  # テストモードボタンを無効化
        test_mode_enabled = False
        test_label.config(bg='gray')
        test_mode_button.config(bg="gray", activebackground="gray")
    else:
        # LED制御が不可能な状態
        toggle_button.config(text="Stopped", bg="lightblue", activebackground="lightblue")
        test_mode_button.config(state=tk.NORMAL)  # テストモードボタンを有効化
        test_label.config(bg='yellow')
        test_mode_button.config(bg="lightblue", activebackground="lightblue")

# テストモードボタンの処理（押している間LEDをオン、離したらオフ）
def press_test_mode():
    global test_mode_led_ON
    if not led_control_enabled:
        test_mode_led_ON = True
        test_mode_button.config(text="ON ", bg="orange", \
                                activebackground="orange")

def release_test_mode():
    global test_mode_led_ON
    if not led_control_enabled:
        test_mode_led_ON = False
        test_mode_button.config(text="OFF", bg="lightblue", \
                                activebackground="lightblue")

# GPIO21ピンからの入力を監視し、LEDを制御するスレッド
def monitor_input():
    global test_mode_led_ON, led_control_enabled, led_control_ON,\
           input_button    
    while True:
        if not led_control_enabled:
            # テストモードかつ入力があるとき
            if test_mode_led_ON or input_button.is_pressed:
                led.on()
            else:
                led.off()
        time.sleep(0.1)  # チェック間隔を設定

# スケジュールをバックグラウンドで実行する関数
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# if __name__ == "__main__":

# センサーの種類を設定します（DHT11またはDHT22）
SENSOR_TYPE = DHT.DHT22
# センサーが接続されているGPIOピン番号を設定します
DHT_PIN = 4

# カウント用変数
pulse_count = 0

# pigpioの初期化
pi = pigpio.pi()
if not pi.connected:
    print("Failed to connect to pigpio.")
    exit()

# GPIO15を入力ピンとして設定
PULSE_GPIO_PIN = 15
pi.set_mode(PULSE_GPIO_PIN, pigpio.INPUT)

# GPIO15の状態変化を検出してカウントするコールバックを設定
pi.callback(PULSE_GPIO_PIN, pigpio.RISING_EDGE, count_pulses)

fig = Figure(figsize=(5, 3), dpi=100)
ax1 = fig.add_subplot(111)
# グラフの初期化
# fig, ax1 = plt.subplots(figsize=(5, 3)) # プロットのサイズを5x3に設定
ax2 = ax1.twinx()  # 2つ目のy軸を追加

# 最大で12時間分のデータを保持するためのリスト
MAX_DATA_POINTS = 24 * 60 // 5  # 24時間分のデータ（5分間隔でデータ取得）
# MAX_DATA_POINTS_Graph = 12 * 60 // 5  # 12時間分のデータ（5分間隔でデータ取得）

# MAX_DATA_POINTS = 12 * 60 // 5  # 12時間分のデータ（5分間隔でデータ取得）
data = []

x_data_sub = []
temp_sub = []
water_temp_sub = []
hum_sub = []

current_time = time.perf_counter_ns()
notFirstTime = False
water_temperature = None  # 初期化
date_data = None   # 初期化

# GPIO20に接続されたLEDのインスタンスを作成
led = LED(20)
led_control_enabled = False
led_control_ON = False
led_already_on = False
test_mode_enabled = True
test_mode_led_ON = False

# GPIO21に接続されたタクトスイッチのインスタンスを作成し、プルアップを有効にする
input_button = Button(21, pull_up=True)

# 現在の時刻を分に変換
now = datetime.now()
led_on_time = now.hour * 60 + now.minute - 1

now = datetime.now()
current_time = now.hour * 60 + now.minute

# 毎分チェックするスケジュールを設定
schedule.every(1).minutes.do(check_and_turn_on_led)

# スレッドを開始してGPIO21の入力を監視
thread_monitor = threading.Thread(target=monitor_input)
# メインプログラム終了時にスレッドも終了させるためデーモンにする
thread_monitor.daemon = True
thread_monitor.start()

# スケジュールをバックグラウンドスレッドで実行
schedule_thread = threading.Thread(target=run_schedule, daemon=True)
schedule_thread.start()

# Tkinter GUIのセットアップ
root = tk.Tk()
root.title("Monitor for Goldfish Cooler with Autofeeder")
root.geometry("540x360")

# 上部フレーム：テキストを表示する領域
text_frame = ttk.Frame(root, padding="1")
text_frame.pack(side=tk.TOP, fill=tk.X)

open_file_button = ttk.Button(text_frame, text="Open Files", command=open_file)
open_file_button.pack(side=tk.LEFT, padx=1, pady=1)

save_button = ttk.Button(text_frame, text="Save Data", command=save_data)
save_button.pack(side=tk.LEFT, padx=1, pady=1)

date_label = ttk.Label(text_frame, text="Data Date: Not loaded")
date_label.pack(side=tk.LEFT, padx=5)

# フレームを作成し、その中にラベルとボタンを横並びで配置
# feeder_frame = tk.Frame(root)
# feeder_frame.pack()

# "Autofeeder"ラベルの設定
led_label = tk.Label(text_frame, text="Autofeeder", font=("Arial", 10), \
     bg='yellow')
led_label.pack(side=tk.LEFT)

# 切り替えボタンを"Autofeeder"ラベルの横に配置
toggle_button = tk.Button(text_frame, text="Stopped", command=\
                    toggle_led_control, bg="lightblue", \
        activebackground="lightblue")
toggle_button.pack(side=tk.LEFT, padx=5)

# "Test Mode"ラベルの設定
test_label = tk.Label(text_frame, text="Test", font=("Arial", 10), \
      bg='yellow')
test_label.pack(side=tk.LEFT)

# テストモードボタンの設定
test_mode_button = tk.Button(text_frame, text="OFF",bg="lightblue",
             activebackground="lightblue", state=tk.NORMAL)
test_mode_button.bind("<ButtonPress>", lambda event: press_test_mode())
test_mode_button.bind("<ButtonRelease>", lambda event: release_test_mode())
test_mode_button.pack()

# 中央フレーム：グラフを表示する領域
plot_frame = ttk.Frame(root, padding="1")
plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# 情報ラベルの追加
info_frame = ttk.Frame(root, padding="1")
info_frame.pack(side=tk.BOTTOM, fill=tk.X)

temp_label = tk.Label(info_frame, font=('Helvetica', 12), bg='white')
temp_label.pack(side=tk.LEFT, padx=3)

hum_label = tk.Label(info_frame, font=('Helvetica', 12), bg='white')
hum_label.pack(side=tk.LEFT, padx=3)

water_temp_label = tk.Label(info_frame, font=('Helvetica', 12), bg='white')
water_temp_label.pack(side=tk.LEFT, padx=3)

try:
    checkTodayCsvFiles()

    collect_data()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    tk.mainloop()
except KeyboardInterrupt:
    print("Exiting program")
finally:
    pi.stop()

