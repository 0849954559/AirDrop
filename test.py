import PySimpleGUI as sg
import subprocess
import pyautogui
import time
import json
import os
import random

# Cấu hình chung
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'profiles.json')
ADDRESS_FILE = os.path.join(BASE_DIR, 'addresses.txt')
IMAGE_PATH = os.path.join(BASE_DIR, "images", "sonic")
CONFIDENCE_LEVEL = 0.7  # Mức độ nhận diện ảnh mặc định

# =========================== HÀM CHÍNH ===========================

def create_layout():
    """Tạo giao diện chính"""
    return [
        [sg.Text('Tool Airdrop', font=('Arial', 14, 'bold'))],
        [sg.Text('Google Profile', size=(15, 1)), sg.InputText(key='Google Profile')],
        [sg.Text('Crypto Wallet Password', size=(15, 1)), sg.InputText(key='Crypto Wallet Password', password_char='*')],
        [sg.Button('Open Profile'), sg.Exit()]
    ]


def find_chrome_path():
    """Tìm đường dẫn Chrome tự động."""
    possible_paths = [
        os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\Application\chrome.exe'),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe") as key:
            chrome_path, _ = winreg.QueryValueEx(key, "")
            if os.path.exists(chrome_path):
                return chrome_path
    except FileNotFoundError:
        pass

    return None


def open_chrome_with_profile(profile_name):
    """Mở Chrome với profile chỉ định."""
    chrome_path = find_chrome_path()
    if not chrome_path:
        print("Chrome không tìm thấy! Kiểm tra lại cài đặt.")
        return
    subprocess.Popen([
        chrome_path, f'--profile-directory={profile_name}', '--new-window', '--start-maximized',
        'https://www.google.com'
    ])

def locate_and_click(image_name, retries=5, confidence=CONFIDENCE_LEVEL, wait_time=2):
    """Tìm và click vào ảnh"""
    img_path = os.path.join(IMAGE_PATH, image_name)
    if not os.path.exists(img_path):
        sg.popup_error(f"File ảnh '{image_name}' không tồn tại: {img_path}")
        return False

    time.sleep(wait_time)  # Chờ trước khi tìm ảnh

    for _ in range(retries):
        location = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
        if location:
            x, y = location
            pyautogui.moveTo(x, y, duration=1)
            pyautogui.click()
            print(f"Clicked on '{image_name}' at ({x}, {y})")
            return True
        time.sleep(1)

    # Chụp ảnh màn hình để debug nếu không tìm thấy ảnh
    pyautogui.screenshot("debug_screen.png")
    print("Screenshot saved as debug_screen.png")
    sg.popup_error(f"Không tìm thấy '{image_name}'. Hãy kiểm tra lại.")
    return False

def enter_password(password):
    """Nhập mật khẩu"""
    time.sleep(5)
    pyautogui.typewrite(password, interval=0.05)
    pyautogui.press('enter')

def get_random_address():
    """Lấy một địa chỉ ngẫu nhiên từ file"""
    if not os.path.exists(ADDRESS_FILE):
        sg.popup_error(f"File 'addresses.txt' không tồn tại: {ADDRESS_FILE}")
        return None

    with open(ADDRESS_FILE, "r", encoding="utf-8") as file:
        addresses = [line.strip() for line in file if line.strip()]

    return random.choice(addresses) if addresses else None

def enter_address():
    """Nhập địa chỉ ví từ file"""
    address = get_random_address()
    if address:
        time.sleep(1)
        pyautogui.typewrite(address, interval=0.01)
        print(f"Đã nhập địa chỉ: {address}")
    else:
        print("Không có địa chỉ để nhập!")

def enter_random_amount():
    """Nhập số lượng token ngẫu nhiên (0.00000x)"""
    time.sleep(1)
    random_number = f"0.00000{random.randint(1, 9)}"
    pyautogui.typewrite(random_number, interval=0.01)
    print(f"Entered amount: {random_number}")

# =========================== CHẠY TOOL ===========================

# Load previous data if exists
try:
    with open(DATA_FILE, 'r') as file:
        profiles_data = json.load(file)
except FileNotFoundError:
    profiles_data = []

# Tạo giao diện
window = sg.Window('Dynamic Entry Form', create_layout(), finalize=True)

while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == 'Open Profile':
        google_profile = values['Google Profile']
        wallet_password = values['Crypto Wallet Password']

        if not google_profile or not wallet_password:
            sg.popup("Vui lòng nhập Google Profile và Wallet Password.")
            continue

        # Lưu dữ liệu vào JSON
        entry = {"Chrome Profile": google_profile, "Crypto Wallet Password": wallet_password}
        profiles_data.append(entry)
        with open(DATA_FILE, 'w') as file:
            json.dump(profiles_data, file, indent=4)

        # Chạy quy trình tự động hóa
        open_chrome_with_profile(google_profile)
        time.sleep(2)  # Đảm bảo Chrome đã mở
        locate_and_click("backpack_icon.png", confidence=0.9)  # Click vào ví
        enter_password(wallet_password)
        locate_and_click("send.png", confidence=0.8)
        locate_and_click("sol.png", confidence=0.8)
        locate_and_click("address.png", confidence=0.8)
        enter_address()
        locate_and_click("next.png", confidence=0.8)
        enter_random_amount()
        locate_and_click("review.png", confidence=0.8)
        locate_and_click("approve.png", confidence=0.7)
        time.sleep(1.5)
        locate_and_click("done.png", confidence=0.8)

window.close()
