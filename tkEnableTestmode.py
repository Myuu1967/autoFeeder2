import tkinter as tk
from gpiozero import LED, Button
import threading
import time

# GPIO20に接続されたLEDのインスタンスを作成
led = LED(20)
test_mode_enabled = False  # 初期状態はテストモードではない
test_mode_led_ON = False

# GPIO21に接続されたタクトスイッチのインスタンスを作成し、プルアップを有効にする
# pull_up=True によりプルアップ抵抗を有効化
input_button = Button(21, pull_up=True)

# tkinter GUIの設定
root = tk.Tk()
root.title("LED Control with Test Mode")
root.geometry("480x300")

# 切り替えボタンの状態を管理する変数
led_control_enabled = False

# LEDオンオフの切り替えボタンの処理
def toggle_led_control():
    global led_control_enabled, test_mode_enabled
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
        test_mode_button.config(text="ON ", bg="orange", activebackground="orange")

def release_test_mode():
    global test_mode_led_ON
    if not led_control_enabled:
        test_mode_led_ON = False
        test_mode_button.config(text="OFF", bg="lightblue", activebackground="lightblue")

# GPIO21ピンからの入力を監視し、LEDを制御するスレッド
def monitor_input():
    global test_mode_led_ON
    while True:
        # テストモードかつ入力があるとき
        if (test_mode_led_ON or input_button.is_pressed)and\
           (not led_control_enabled):
            led.on()
        else:
            led.off()
        time.sleep(0.1)  # チェック間隔を設定

# スレッドを開始してGPIO21の入力を監視
thread = threading.Thread(target=monitor_input)
thread.daemon = True  # メインプログラム終了時にスレッドも終了させるためデーモンにする
thread.start()

# フレームを作成し、その中にラベルとボタンを横並びで配置
frame = tk.Frame(root)
frame.pack()

# "LED"ラベルの設定
led_label = tk.Label(frame, text="Autofeeder", font=("Arial", 10), bg='yellow')
led_label.pack(side=tk.LEFT, padx=5)

# 切り替えボタンを"LED"ラベルの横に配置
toggle_button = tk.Button(frame, text="Stopped", command=toggle_led_control,
                          bg="lightblue", activebackground="lightblue")
toggle_button.pack(side=tk.LEFT)

# "Test Mode"ラベルの設定
test_label = tk.Label(frame, text="Test", font=("Arial", 10), bg='yellow')
test_label.pack(side=tk.LEFT, padx=5)

# テストモードボタンの設定
test_mode_button = tk.Button(frame, text="OFF",bg="lightblue",
                             activebackground="lightblue", state=tk.NORMAL)
test_mode_button.bind("<ButtonPress>", lambda event: press_test_mode())
test_mode_button.bind("<ButtonRelease>", lambda event: release_test_mode())
test_mode_button.pack(pady=20)

# メインループの開始
root.mainloop()

