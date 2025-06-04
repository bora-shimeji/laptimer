import time
import sys

# --- 定数定義 (変更なし) ---
GPIO_PIN = 19
PROTOMATTER_WIDTH = 128
PROTOMATTER_HEIGHT = 64

# --- グローバル変数 (変更なし) ---
TKINTER_AVAILABLE = False
GPIO_AVAILABLE = False
MATRIX_AVAILABLE = False

# --- Tkinterのインポート試行 (変更なし) ---
try:
    import tkinter as tk
    from tkinter import font
    TKINTER_AVAILABLE = True
    print("Tkinterモジュールが正常にインポートされました。")
except ImportError:
    print("Tkinterモジュールが見つかりません。GUI機能は無効になります。", file=sys.stderr)
except Exception as e:
    print(f"Tkinterモジュールのインポート中に予期せぬエラー: {e}。GUI機能は無効。", file=sys.stderr)

# --- 他のライブラリインポート試行 (変更なし) ---
if True:
    try:
        import RPi.GPIO as GPIO
        GPIO_AVAILABLE = True
        print("RPi.GPIOモジュールが正常にインポートされました。")
    except ImportError: print("RPi.GPIOモジュールが見つかりません。GPIO機能は無効になります。", file=sys.stderr)
    except RuntimeError as e: print(f"RPi.GPIOモジュールのロード中にRuntimeError: {e}。GPIO機能は無効。", file=sys.stderr)
    except Exception as e: print(f"RPi.GPIOモジュールのインポート中に予期せぬエラー: {e}。GPIO機能は無効。", file=sys.stderr)
    try:
        import adafruit_protomatter, raspberrypi_piomatter, board, bitbangio, displayio, terminalio
        from adafruit_display_text import label
        MATRIX_AVAILABLE = True
        print("Protomatter (LEDマトリクス)関連ライブラリがインポートされました。")
    except ImportError as e: print(f"Protomatter関連ライブラリのインポートに失敗: {e}。LEDマトリクス機能は無効。", file=sys.stderr)
    except Exception as e: print(f"Protomatter関連ライブラリのインポート中に予期せぬエラー: {e}。LEDマトリクス機能は無効。", file=sys.stderr)

# --- アプリケーションの状態定義 (変更なし) ---
class AppState:
    READY = "READY"
    MEASURING = "MEASURING"
    TIMING = "TIMING"

# --- LEDMatrixControllerクラス (変更なしなので省略) ---
class LEDMatrixController:
    def __init__(self, width=PROTOMATTER_WIDTH, height=PROTOMATTER_HEIGHT):
        self.width=width; self.height=height; self.matrix_instance=None; self.display_obj=None; self.text_group=None; self.text_label=None; self.current_text_on_matrix=""
        if MATRIX_AVAILABLE: print("LEDMatrixController: Protomatter初期化試行..."); # 簡略化
        else: print("LEDMatrixController: Matrix機能無効。初期化スキップ。"); return
        try:
            addr_pin_names = ['A0','A1','A2','A3','A4'] if self.height > 32 else (['A0','A1','A2','A3'] if self.height > 16 else ['A0','A1','A2'])
            addr_pins_actual = [getattr(board, pin) for pin in addr_pin_names]
            rgb_pins_actual = [board.GP2, board.GP3, board.GP4, board.GP5, board.GP6, board.GP7]; clock_pin_actual = board.GP11; latch_pin_actual = board.GP12; output_enable_pin_actual = board.GP13
            self.matrix_instance = raspberrypi_piomatter.RaspberryPiProtomatter(self.width,self.height,6,rgb_pins=rgb_pins_actual,addr_pins=addr_pins_actual,clock_pin=clock_pin_actual,latch_pin=latch_pin_actual,output_enable_pin=output_enable_pin_actual,user_preserved_gpios=raspberrypi_piomatter.PRESERVE_GPIO_NONE)
            self.display_obj=self.matrix_instance.display; self.text_group=displayio.Group()
            self.text_label=label.Label(terminalio.FONT,text="INIT",color=0xFFFFFF,anchor_point=(0.5,0.5),anchored_position=(self.width//2,self.height//2)); self.text_group.append(self.text_label); self.display_obj.show(self.text_group); self.current_text_on_matrix="INIT"; print("LEDMatrixController: Protomatter初期化成功。")
        except Exception as e: print(f"LEDMatrixController: Protomatter初期化エラー: {e}", file=sys.stderr); self.matrix_instance=None
    def show_text(self,text_to_display,color=0xFFFFFF):
        self.current_text_on_matrix = text_to_display
        if not self.matrix_instance: return
        try: self.text_label.text=text_to_display; self.text_label.color=color; self.display_obj.refresh(minimum_frames_per_second=0)
        except Exception as e: print(f"LEDMatrixController: テキスト表示エラー: {e}", file=sys.stderr)
    def clear(self): print("LEDMatrixController: clear()呼び出し。"); self.show_text("")

# --- SensorHandlerクラス (変更なしなので省略) ---
class SensorHandler:
    def __init__(self, app_instance, pin_number=GPIO_PIN):
        self.app = app_instance; self.pin_number = pin_number; self.debounce_time_ms = 1000
        if GPIO_AVAILABLE: print(f"SensorHandler: GPIO {self.pin_number} 初期化試行..."); # 簡略化
        else: print("SensorHandler: GPIO機能無効。初期化スキップ。"); return
        try: GPIO.setmode(GPIO.BCM); GPIO.setup(self.pin_number, GPIO.IN, pull_up_down=GPIO.PUD_UP); print("SensorHandler: GPIO初期化成功")
        except Exception as e: print(f"SensorHandler: GPIO初期化エラー: {e}", file=sys.stderr)
    def start_monitoring(self):
        if GPIO_AVAILABLE: print(f"SensorHandler: GPIO {self.pin_number} 監視開始試行..."); # 簡略化
        else: print("SensorHandler: GPIO機能無効。監視開始不可。"); return
        try: GPIO.remove_event_detect(self.pin_number)
        except: pass
        try: GPIO.add_event_detect(self.pin_number, GPIO.FALLING, callback=self._gpio_event_callback, bouncetime=self.debounce_time_ms); print("SensorHandler: GPIO監視開始成功")
        except Exception as e: print(f"SensorHandler: GPIO監視開始エラー: {e}", file=sys.stderr)
    def stop_monitoring(self):
        if GPIO_AVAILABLE: print(f"SensorHandler: GPIO {self.pin_number} 監視停止試行..."); # 簡略化
        else: print("SensorHandler: GPIO機能無効。監視停止不可。"); return
        try: GPIO.remove_event_detect(self.pin_number); print("SensorHandler: GPIO監視停止成功")
        except Exception as e: print(f"SensorHandler: GPIO監視停止エラー: {e}", file=sys.stderr)
    def _gpio_event_callback(self, channel):
        print(f"SensorHandler: GPIO {channel} トリガー検知。")
        if self.app and hasattr(self.app, 'root') and self.app.root: # Tkinterの場合
            if TKINTER_AVAILABLE and self.app.root.winfo_exists(): self.app.root.after(0, self.app.handle_sensor_trigger)
            # CUIテストの場合、self.app.rootは存在しないので、直接呼び出す
            elif not TKINTER_AVAILABLE and hasattr(self.app, 'handle_sensor_trigger'): self.app.handle_sensor_trigger()
            else: print("SensorHandler: rootウィンドウなし、またはhandle_sensor_triggerなし。呼出不可。", file=sys.stderr)
        elif self.app and hasattr(self.app, 'handle_sensor_trigger'): # CUIテストでappがrootを持たない場合
             self.app.handle_sensor_trigger()
        else: print("SensorHandler: appインスタンスまたはhandle_sensor_triggerなし。", file=sys.stderr)
    def cleanup(self):
        if GPIO_AVAILABLE: print("SensorHandler: GPIOクリーンアップ (現時点では具体的な処理なし)")
        else: print("SensorHandler: GPIO機能無効。クリーンアップスキップ。");

# --- メインアプリケーションクラス (SensorApp) ---
if TKINTER_AVAILABLE:
    class SensorApp:
        def __init__(self, tk_root):
            self.root = tk_root
            self.root.title("光電センサー時間計測")
            self.root.geometry("400x250")
            self.current_state = AppState.READY
            self.led_text_var = tk.StringVar(value="")
            self.measurement_start_time = None
            self.timer_update_id = None
            self.led_controller = LEDMatrixController()
            self.sensor_handler = SensorHandler(self)

            # GUI要素作成 (変更なしなので簡略化)
            try: self.btn_font = font.Font(family="Arial", size=12, weight="bold"); self.gui_led_font = font.Font(family="Courier New", size=16, weight="bold")
            except tk.TclError: self.btn_font = font.nametofont("TkDefaultFont"); self.gui_led_font = font.nametofont("TkTextFont"); self.gui_led_font.config(size=14)
            self.gui_led_label = tk.Label(self.root, textvariable=self.led_text_var, font=self.gui_led_font, bg="#333333", fg="#00FF00", width=20, height=2, relief=tk.SUNKEN, bd=2, anchor="center"); self.gui_led_label.pack(pady=20, padx=10, fill=tk.X)
            btn_frame = tk.Frame(self.root); btn_frame.pack(pady=10)
            self.start_btn = tk.Button(btn_frame, text="計測開始", command=self.action_start_measurement, font=self.btn_font, width=12, height=2, bg="#4CAF50", fg="white", relief=tk.RAISED, bd=3); self.start_btn.pack(side=tk.LEFT, padx=12)
            self.stop_btn = tk.Button(btn_frame, text="計測終了", command=self.action_stop_measurement, font=self.btn_font, width=12, height=2, state=tk.DISABLED, bg="#f44336", fg="white", relief=tk.RAISED, bd=3); self.stop_btn.pack(side=tk.LEFT, padx=12)
            self.root.protocol("WM_DELETE_WINDOW", self._handle_window_close)
            self._update_led_panel_text("READY")
            self._update_button_ui_state()

        def _handle_window_close(self):
            print("SensorApp: ウィンドウクローズ処理開始...")
            if self.timer_update_id: self.root.after_cancel(self.timer_update_id); self.timer_update_id = None
            if self.sensor_handler: self.sensor_handler.stop_monitoring(); self.sensor_handler.cleanup()
            if self.led_controller: self.led_controller.clear()
            if self.root and self.root.winfo_exists(): self.root.destroy()
            print("SensorApp: ウィンドウクローズ処理完了。")

        def action_start_measurement(self):
            print(f"SensorApp: 「計測開始」ボタンクリック。現在の状態: {self.current_state}")
            if self.current_state == AppState.READY:
                self.current_state = AppState.MEASURING
                print(f"SensorApp: 状態変更 -> {self.current_state}")
                self._update_led_panel_text("MEASURE")
                self._update_button_ui_state()
                if self.sensor_handler:
                    print("SensorApp: センサー監視を開始します...")
                    self.sensor_handler.start_monitoring()
                else:
                    print("SensorApp: SensorHandlerが初期化されていません。", file=sys.stderr)
                self.measurement_start_time = None # 最初のセンサー入力で設定される
                print("SensorApp: 計測開始準備完了。最初のセンサー入力を待っています。")
            else:
                print(f"SensorApp: 現在の状態 ({self.current_state}) では計測を開始できません。", file=sys.stderr)

        def action_stop_measurement(self):
            # (このメソッドはステップ8で実装)
            print(f"SensorApp: 「計測終了」ボタンクリック。現在の状態: {self.current_state}")
            if self.timer_update_id: self.root.after_cancel(self.timer_update_id); self.timer_update_id = None
            self.current_state = AppState.READY
            self._update_led_panel_text("READY")
            self._update_button_ui_state()
            if self.sensor_handler: self.sensor_handler.stop_monitoring()
            print("SensorApp: 計測終了処理完了。READY状態に戻りました。")

        def handle_sensor_trigger(self):
            # (このメソッドはステップ6で実装)
            print(f"SensorApp: handle_sensor_trigger呼び出し。状態: {self.current_state}")
            if self.current_state == AppState.MEASURING: self.current_state = AppState.TIMING; self._update_led_panel_text("0:00.000") # 仮
            elif self.current_state == AppState.TIMING: self.current_state = AppState.MEASURING; self._update_led_panel_text("MEASURE") # 仮

        def _update_button_ui_state(self):
            # (変更なしなので簡略化)
            is_ready = self.current_state == AppState.READY
            self.start_btn.config(state=tk.NORMAL if is_ready else tk.DISABLED); self.stop_btn.config(state=tk.DISABLED if is_ready else tk.NORMAL)
            # print(f"SensorApp: ボタン状態更新 Start={self.start_btn['state']}, Stop={self.stop_btn['state']}")

        def _update_led_panel_text(self, text_to_display):
            # (変更なしなので簡略化)
            self.led_text_var.set(text_to_display)
            if self.led_controller: self.led_controller.show_text(text_to_display)
            # print(f"SensorApp: LED表示更新 -> {text_to_display}")
else:
    print("Tkinterが無効なため、SensorAppクラスは定義されません。", file=sys.stderr)
    SensorApp = None

def run_gui_application():
    # (変更なしなので省略)
    if not TKINTER_AVAILABLE or SensorApp is None: return None, None
    root_window = None; app_obj = None
    try: root_window = tk.Tk(); app_obj = SensorApp(root_window); print("SensorAppインスタンス作成完了。"); root_window.mainloop(); print("Tkinter mainloop正常終了。");
    except Exception as e: print(f"GUIアプリ実行エラー: {e}", file=sys.stderr);
    finally:
        if root_window and root_window.winfo_exists(): root_window.destroy()
    return root_window, app_obj

# --- エントリーポイント ---
if __name__ == '__main__':
    exit_code = 0
    print(f"--- アプリケーション開始: Tkinter利用可能={TKINTER_AVAILABLE}, GPIO利用可能={GPIO_AVAILABLE}, Matrix利用可能={MATRIX_AVAILABLE} ---")

    if TKINTER_AVAILABLE and SensorApp is not None:
        _, app_instance_from_gui = run_gui_application()
        if app_instance_from_gui is None: exit_code = 1 # 早期終了やエラーの場合
    else:
        print("GUIが利用できないため、CUIモードで action_start_measurement のロジックテストを試みます。", file=sys.stderr)
        # CUIテスト用の仮オブジェクトと状態
        class MockAppForCUITesting:
            def __init__(self):
                self.current_state = AppState.READY
                self.sensor_handler = SensorHandler(self) # SensorHandlerに自身を渡す
                self.led_controller = LEDMatrixController()
                self.measurement_start_time = None
                print("MockAppForCUITesting: 初期化完了。")

            def _update_led_panel_text(self, text):
                # LEDMatrixControllerの実際のshow_textを呼び出す
                if self.led_controller: self.led_controller.show_text(text)
                print(f"MockAppForCUITesting: LED表示更新 -> {text} (LED Controller Text: {self.led_controller.current_text_on_matrix if self.led_controller else 'N/A'})")

            def _update_button_ui_state(self):
                print(f"MockAppForCUITesting: ボタン状態更新 (仮)。現在の状態: {self.current_state}")

            def action_start_measurement(self):
                print(f"MockAppForCUITesting: 「計測開始」アクション。現在の状態: {self.current_state}")
                if self.current_state == AppState.READY:
                    self.current_state = AppState.MEASURING
                    print(f"MockAppForCUITesting: 状態変更 -> {self.current_state}")
                    self._update_led_panel_text("MEASURE")
                    self._update_button_ui_state()
                    if self.sensor_handler:
                        print("MockAppForCUITesting: SensorHandler.start_monitoring() を呼び出します。")
                        self.sensor_handler.start_monitoring()
                    self.measurement_start_time = None
                    print("MockAppForCUITesting: 計測開始準備完了。")
                else:
                    print(f"MockAppForCUITesting: 現在の状態 ({self.current_state}) では計測を開始できません。", file=sys.stderr)

            def handle_sensor_trigger(self): # SensorHandlerから呼び出されるメソッド
                 print(f"MockAppForCUITesting: handle_sensor_trigger呼び出し。状態: {self.current_state}")
                 if self.current_state == AppState.MEASURING:
                     self.current_state = AppState.TIMING
                     self._update_led_panel_text("0:00.000")
                 elif self.current_state == AppState.TIMING:
                     self.current_state = AppState.MEASURING
                     self._update_led_panel_text("MEASURE")

        try:
            print("CUIテスト: MockAppインスタンス作成...")
            cui_app = MockAppForCUITesting()
            print("CUIテスト: cui_app.action_start_measurement() 呼び出し...")
            cui_app.action_start_measurement()
            print(f"CUIテスト: 呼び出し後の状態: {cui_app.current_state}")
            if cui_app.current_state != AppState.MEASURING:
                print("CUIテストエラー: action_start_measurement後の状態がMEASURINGではありません。", file=sys.stderr)
                exit_code = 1

            if not GPIO_AVAILABLE:
                print("CUIテスト: GPIO無効なので、擬似的にSensorHandlerのコールバックを呼び出します...")
                if cui_app.sensor_handler:
                    print("CUIテスト: cui_app.sensor_handler._gpio_event_callback(GPIO_PIN) を擬似的に呼び出し (1回目)")
                    cui_app.sensor_handler._gpio_event_callback(GPIO_PIN) # MEASURING -> TIMING
                    print(f"CUIテスト: 1回目トリガー後の状態: {cui_app.current_state}")
                    if cui_app.current_state != AppState.TIMING:
                         print("CUIテストエラー: 1回目トリガー後の状態がTIMINGではありません。", file=sys.stderr); exit_code = 1
                else:
                    print("CUIテストエラー: cui_app.sensor_handlerが初期化されていません。", file=sys.stderr)


        except Exception as e:
            print(f"CUIモードでの action_start_measurement テスト中にエラー: {e}", file=sys.stderr)
            exit_code = 1

    print(f"--- アプリケーション終了 (終了コード: {exit_code}) ---")
