import json
import os
import random
import subprocess
import time
import winreg
import PySimpleGUI as sg
import psutil
import pyautogui
import pyscreeze

# Cấu hình chung
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'profiles.json')
ADDRESS_FILE = os.path.join(BASE_DIR, 'addresses.txt')
IMAGE_PATH = os.path.join(BASE_DIR, "images", "sonic")
CONFIDENCE_LEVEL = 0.7  # Mức độ nhận diện ảnh mặc định
BUTTON_IMAGE = 'approvebox.png'  # Ảnh của nút cần bấm
DISAPPEAR_TIME = 60  # Thời gian tối đa trước khi dừng tìm kiếm

# =========================== HÀM CHÍNH ===========================

def create_layout():
    """Tạo giao diện chính"""
    return [
        [sg.Text('Tool Airdrop', font=('Arial', 14, 'bold'))],
        [sg.Text('Google Profile', size=(15, 1)), sg.InputText(key='Google Profile')],
        [sg.Text('backpack pass', size=(15, 1)),
         sg.InputText(key='backpack pass', password_char='*')],
        [sg.Text('TX quantity', size=(15, 1)), sg.InputText(key='Num Transactions', size=(5, 1))],
        [sg.Checkbox('Check in', default=True, key='EnableCheckIn')],  # ✅ Checkbox for check-in
        [sg.Checkbox('Enable Open Box', default=True, key='EnableOpenBox')],  # ✅ Checkbox for open box
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
    subprocess.Popen([chrome_path, f'--profile-directory={profile_name}', '--new-window', '--start-maximized',
                      'https://www.google.com'])


def close_chrome():
    """Đóng tất cả các tiến trình Chrome sau khi giao dịch hoàn thành."""
    print("Closing Google Chrome...")
    for process in psutil.process_iter(attrs=['pid', 'name']):
        if "chrome" in process.info['name'].lower():
            try:
                process_pid = process.info['pid']
                psutil.Process(process_pid).terminate()  # Terminate Chrome
                print(f"Closed Chrome process (PID: {process_pid})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

def locate_and_click(image_name, retries=5, confidence=CONFIDENCE_LEVEL, wait_time=1):
    """Tìm và click vào ảnh với xử lý lỗi."""
    img_path = os.path.join(IMAGE_PATH, image_name)
    if not os.path.exists(img_path):
        sg.popup_error(f"File ảnh '{image_name}' không tồn tại: {img_path}")
        return False

    time.sleep(wait_time)  # Chờ trước khi tìm ảnh

    for attempt in range(retries):
        try:
            location = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if location:
                x, y = location
                pyautogui.moveTo(x, y, duration=0.75)
                pyautogui.click()
                print(f"Clicked on '{image_name}' at ({x}, {y})")
                return True
        except pyautogui.ImageNotFoundException:
            print(f"Attempt {attempt+1}/{retries}: '{image_name}' not found, retrying...")
        time.sleep(0.5)

    pyautogui.screenshot("debug_screen.png")
    print(f"Không tìm thấy '{image_name}', đã lưu ảnh màn hình debug_screen.png")
    return False


def enter_password(password):
    """Nhập mật khẩu"""
    time.sleep(4)
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


def run_checkin():
    if enable_checkin:
        print("Check-in feature is enabled.")
        pyautogui.hotkey('F5')  # Open a new tab in the browser
        time.sleep(1)  # Wait for the new tab to open
        pyautogui.hotkey('ctrl', 'l')  # Focus on the address bar (Ctrl + L)
        pyautogui.typewrite("https://odyssey.sonic.game/task/check-in")  # Type the website URL
        pyautogui.press('enter')  # Press Enter to open the website
        time.sleep(2)
        pyautogui.moveTo(960, 540, duration=1)
        time.sleep(3.5)
        pyautogui.scroll(-500)
        locate_and_click("checkin.png", confidence=0.8)
        time.sleep(2.5)
        locate_and_click("approvecheckin.png", confidence=0.8)
        time.sleep(1)
        locate_and_click("backpack_icon.png", confidence=0.8)
    else:
        print("Check-in feature is disabled. Skipping check-in process.")

def claim_box():
    pyautogui.hotkey('ctrl', 'l')  # Focus on the address bar (Ctrl + L)
    pyautogui.typewrite("https://odyssey.sonic.game/task/milestone")  # Type the website URL
    pyautogui.press('enter')  # Press Enter to open the website
    time.sleep(2)
    pyautogui.moveTo(960, 540, duration=1)
    time.sleep(1.5)
    pyautogui.scroll(-500)
    locate_and_click("claim2.png", confidence=0.9)
    locate_and_click("claim4.png", confidence=0.9)
    locate_and_click("claim6.png", confidence=0.9)

def open_box():
    pyautogui.hotkey('ctrl', 'l')  # Focus on the address bar (Ctrl + L)
    pyautogui.typewrite("https://odyssey.sonic.game/task/milestone")  # Type the website URL
    pyautogui.press('enter')  # Press Enter to open the website
    time.sleep(1)
    pyautogui.moveTo(960, 540, duration=1)
    locate_and_click("down.png", confidence=0.8)
    time.sleep(0.5)
    locate_and_click("open_box.png", confidence=0.8)
    time.sleep(0.5)
    locate_and_click("all.png", confidence=0.8)
    time.sleep(0.5)
    locate_and_click("open.png", confidence=0.8)
    enter_password(wallet_password)
    time.sleep(4)
    process_transaction()

def repeat_transaction( num_transactions):
    """Giao dịch lặp lại và nếu có lỗi, nó sẽ thử lại một lần trước khi bỏ qua"""
    for i in range(num_transactions):
        success = False  # Biến để kiểm tra nếu giao dịch thành công
        max_attempts = 2  # Số lần thử lại tối đa

        for attempt in range(max_attempts):
            print(f"Thực hiện giao dịch {i + 1}, lần thử {attempt + 1}...")

            if not locate_and_click("send.png", confidence=0.8):
                print("Không tìm thấy nút gửi, thử quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            if not locate_and_click("sol.png", confidence=0.8):
                print("Không tìm thấy loại tiền, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            if not locate_and_click("address.png", confidence=0.8):
                print("Không tìm thấy ô nhập địa chỉ, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            enter_address()  # Nhập địa chỉ ví

            if not locate_and_click("next.png", confidence=0.8):
                print("Không tìm thấy nút tiếp theo, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            enter_random_amount()  # Nhập số tiền

            if not locate_and_click("review.png", confidence=0.8):
                print("Không tìm thấy nút review, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            if not locate_and_click("approve.png", confidence=0.8):
                print("Không tìm thấy nút approve, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            time.sleep(1.5)  # Đợi giao dịch hoàn thành

            if not locate_and_click("done.png", confidence=0.8):
                print("Không tìm thấy nút hoàn thành, quay lại...")
                locate_and_click("return.png", confidence=0.8) or locate_and_click("x.png", confidence=0.8)
                continue

            success = True  # Giao dịch hoàn thành thành công
            print(f"Giao dịch {i + 1} hoàn thành.")
            break  # Thoát khỏi vòng lặp thử lại

        if not success:
            print(f"Giao dịch {i + 1} thất bại sau {max_attempts} lần thử. Chuyển sang giao dịch tiếp theo.")

        # Đợi trước khi thử giao dịch tiếp theo
        time.sleep(0.5)

def locate_and_click_with_timer(image_name, confidence=CONFIDENCE_LEVEL):
    """Locate and click an image repeatedly until it disappears or times out."""
    img_path = os.path.join(IMAGE_PATH, image_name)
    start_time = time.time()  # Set the initial start time
    has_clicked = False  # Keep track of whether any button was clicked

    if not os.path.exists(img_path):
        print(f"Error: Image file '{img_path}' not found. Please check the IMAGE_PATH and image name.")
        return False

    print(f"Waiting for image '{image_name}' to appear and click...")

    while True:
        # Check if the total elapsed time has exceeded DISAPPEAR_TIME
        elapsed_time = time.time() - start_time
        if elapsed_time > DISAPPEAR_TIME:
            print(
                f"Timeout: Image '{image_name}' did not appear or stay visible long enough for {DISAPPEAR_TIME} seconds.")
            break

        try:
            # Locate the image on the screen
            locations = list(pyautogui.locateAllOnScreen(img_path, confidence=confidence))
            if locations:
                for location in locations:
                    # Click on the center of the located image
                    center = pyautogui.center(location)
                    pyautogui.moveTo(center.x, center.y, duration=0.5)
                    pyautogui.click()
                    print(f"Clicked on '{image_name}' at {center.x}, {center.y}")
                    has_clicked = True

                    # Reset the start time after a successful click to ensure waiting for the next appearance
                    start_time = time.time()

                    # Wait briefly to avoid multiple clicks on the same image
                    time.sleep(0.5)

            else:
                print(f"Image '{image_name}' is not visible. Waiting for it to reappear...")
                # Brief grace period before rechecking
                time.sleep(0.5)
        except pyscreeze.ImageNotFoundException:
            print(f"Error: Unable to locate '{image_name}'. Retrying...")  # Handle exceptions gracefully
            time.sleep(0.5)

    return has_clicked



def process_transaction():
    print("Starting transaction...")
    success = locate_and_click_with_timer(BUTTON_IMAGE, confidence=0.7)
    if success:
        print("Finished processing transaction boxes!")
    else:
        print("Transaction failed: No transaction boxes to process or button not found.")

# =========================== CHẠY TOOL ===========================



try:
    with open(DATA_FILE, 'r') as file:
        profiles_data = json.load(file)
except FileNotFoundError:
    profiles_data = []



# Create the window
window = sg.Window('Dynamic Entry Form', create_layout(), finalize=True)

# Flag to track if the Chrome profile and password have been opened
chrome_opened = False

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == 'Open Profile':
        google_profile = values['Google Profile']
        wallet_password = values['backpack pass']
        enable_checkin = values['EnableCheckIn']  # ✅ Read the "Check-In" checkbox value
        enable_open_box = values['EnableOpenBox']  # ✅ Read the "Enable Open Box" checkbox value

        # Validate that the necessary fields are filled
        if not google_profile or not wallet_password:
            sg.popup("Please enter both the Google Profile and Wallet Password.")
            continue

        # Get the TX quantity from the user input
        try:
            num_transactions = int(values['Num Transactions'])  # Get the TX quantity from the input
            if num_transactions <= 0:
                sg.popup("Please enter a positive number for transactions.")
                continue
        except ValueError:
            sg.popup("Invalid TX quantity. Please enter a valid number.")
            continue

        # Save the data to JSON
        entry = {"Chrome Profile": google_profile, "backpack pass": wallet_password}
        profiles_data.append(entry)
        with open(DATA_FILE, 'w') as file:
            json.dump(profiles_data, file, indent=4)

        # Open Chrome and enter the wallet password only once
        if not chrome_opened:
            open_chrome_with_profile(google_profile)
            time.sleep(4)  # Wait for Chrome to open
            locate_and_click("backpack_icon.png", confidence=0.8)  # Click on send
            enter_password(wallet_password)  # Enter the wallet password once
            chrome_opened = True  # Mark that Chrome has been opened and password entered

        # ✅ Run Check-In only if enabled
        if enable_checkin:
            run_checkin()

        # Transaction repeat
        time.sleep(1.5)
        repeat_transaction( num_transactions)

        claim_box()

        # ❇️ Open Box only if enabled
        if enable_open_box:
            print("Open Box is enabled. Opening boxes...")
            open_box()
        else:
            print("Open Box is disabled. Skipping the Open Box process.")


window.close()


