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

# =========================== Create layout ===========================

def create_initial_layout():
    """Create the first layout to ask for the number of profiles."""
    return [
        [sg.Text('How many profiles do you want to run?', font=('Arial', 14, 'bold'))],
        [sg.InputText(key='Num Profiles', size=(5, 1))],
        [sg.Button('Next'), sg.Exit()]
    ]

def save_profiles(profiles_to_save):
    """Save profiles to the JSON file when Remember checkbox is enabled."""
    with open(DATA_FILE, 'w') as file:
        json.dump(profiles_to_save, file, indent=4)
        print(f"Profiles saved to {DATA_FILE}")

def create_dynamic_layout(num_profiles, saved_profiles=[]):
    """Create a dynamic layout for entering profile data."""
    profile_layout = []
    for i in range(1, num_profiles + 1):
        saved_profile = saved_profiles[i - 1] if len(saved_profiles) >= i else {}

        profile_layout.append([sg.Text(f'Profile {i}', font=('Arial', 12, 'bold'))])
        profile_layout.append(
            [sg.Text('Google Profile', size=(15, 1)),
             sg.InputText(saved_profile.get('Google Profile', ''), key=f'Google Profile {i}')]
        )
        profile_layout.append(
            [sg.Text('Password', size=(15, 1)),
             sg.InputText(saved_profile.get('backpack pass', ''), key=f'backpack pass {i}', password_char='*')]
        )
        profile_layout.append(
            [sg.Text('TX quantity', size=(15, 1)),
             sg.InputText(saved_profile.get('Num Transactions', ''), key=f'Num Transactions {i}', size=(5, 1),
                          disabled=not saved_profile.get('EnableTransactions', False))]
        )
        profile_layout.append(
            [
                sg.Checkbox('Enable Transactions', default=saved_profile.get('EnableTransactions', False),
                            key=f'EnableTransactions {i}', enable_events=True),
                sg.Checkbox('Check in', default=saved_profile.get('EnableCheckIn', False),
                            key=f'EnableCheckIn {i}'),
                sg.Checkbox('Enable Open Box', default=saved_profile.get('EnableOpenBox', False),
                            key=f'EnableOpenBox {i}')
            ]
        )
        # Add "Remember My Password and Profile" checkbox
        profile_layout.append(
            [sg.Checkbox("Remember My Password and Profile", default=bool(saved_profile),
                         key=f"RememberProfile {i}")]
        )
        profile_layout.append([sg.HorizontalSeparator()])

    return [[sg.Column(profile_layout, scrollable=True, vertical_scroll_only=True, size=(600, 400))],
            [sg.Button('Run Profiles'), sg.Exit()]]

def load_saved_profiles():
    """Load profiles from the saved JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"Error loading profiles from {DATA_FILE}. Starting fresh...")
    return []

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
        return None
    process = subprocess.Popen([chrome_path,
                                f'--profile-directory={profile_name}',
                                '--new-window',
                                '--start-maximized',
                                'https://www.google.com'])
    return process  # Return the process object

def close_chrome(chrome_process):
    """Đóng tiến trình Chrome cụ thể đã mở."""
    print("Closing Google Chrome...")
    try:
        chrome_process.terminate()  # Terminate the specific Chrome process
        chrome_process.wait(timeout=5)  # Wait for it to terminate gracefully
        print(f"Closed Chrome process with PID: {chrome_process.pid}")
    except Exception as e:
        print(f"Failed to close Chrome process: {e}")

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
        time.sleep(1.5)

    pyautogui.screenshot("debug_screen.png")
    print(f"Không tìm thấy '{image_name}', đã lưu ảnh màn hình debug_screen.png")
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
        time.sleep(4.5)
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
    time.sleep(2.5)
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


# =========================== MAIN PROGRAM ===========================

saved_profiles = load_saved_profiles()

window = sg.Window('Profile Setup Tool', create_initial_layout(), finalize=True)
profiles_data = []  # Global profile data
num_profiles = len(saved_profiles)  # Pre-fill number of profiles if saved profiles exist

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Exit'):  # Exit condition
        break

    # Handle enabling/disabling the TX quantity field dynamically
    elif event.startswith('EnableTransactions'):
        checkbox_id = event.split(' ')[-1]
        num_tx_key = f'Num Transactions {checkbox_id}'
        if num_tx_key in window.key_dict:
            window[num_tx_key].update(disabled=not values[event], value='' if not values[event] else '')

    # Handle "Next" button press for setting up dynamic layout
    elif event == 'Next':
        try:
            num_profiles = int(values['Num Profiles'])
            if num_profiles <= 0:
                sg.popup("Please enter a positive number for profiles.")
                continue
        except ValueError:
            sg.popup("Invalid number of profiles. Please enter a valid integer.")
            continue

        # Switch to the profile entry form
        window.close()
        window = sg.Window('Dynamic Profile Entry Form',
                           create_dynamic_layout(num_profiles, saved_profiles), finalize=True)

    # Handle "Run Profiles" press
    elif event == 'Run Profiles':
        profiles_data = []  # Reset before processing
        profiles_to_save = []  # Only store profiles with "Remember Me" checked

        for i in range(1, num_profiles + 1):
            google_profile = values.get(f'Google Profile {i}', '').strip()
            wallet_password = values.get(f'backpack pass {i}', '').strip()
            enable_transactions = values.get(f'EnableTransactions {i}', False)
            enable_checkin = values.get(f'EnableCheckIn {i}', False)
            enable_open_box = values.get(f'EnableOpenBox {i}', False)
            remember_profile = values.get(f'RememberProfile {i}', False)

            # Validate transaction count (if enabled)
            num_transactions = 0
            if enable_transactions:
                try:
                    num_transactions = int(values.get(f'Num Transactions {i}', 0))
                except ValueError:
                    sg.popup_error(f"Invalid TX quantity for Profile {i}. Please provide a valid number.")
                    continue

            # Validate essential fields
            if not google_profile or not wallet_password:
                sg.popup_error(f"Profile {i} is missing Google Profile or Password.")
                continue

            # Compile profile data
            profile = {
                "Google Profile": google_profile,
                "backpack pass": wallet_password,
                "EnableTransactions": enable_transactions,
                "EnableCheckIn": enable_checkin,
                "EnableOpenBox": enable_open_box,
                "Num Transactions": num_transactions
            }
            profiles_data.append(profile)

            # Save profile if "Remember Me" is checked
            if remember_profile:
                profiles_to_save.append(profile)

        # Save remembered profiles to file
        save_profiles(profiles_to_save)

        if not profiles_data:
            sg.popup("No valid profiles provided. Please check your inputs.")
            continue

        # Perform processing logic for each profile
        for idx, profile in enumerate(profiles_data):
            try:
                print(f"\n--- Starting Profile {idx + 1}: {profile['Google Profile']} ---")

                # Retrieve profile-specific info
                google_profile = profile["Google Profile"]
                wallet_password = profile["backpack pass"]
                enable_transactions = profile["EnableTransactions"]
                enable_checkin = profile["EnableCheckIn"]
                enable_open_box = profile["EnableOpenBox"]
                num_transactions = profile["Num Transactions"]

                # Open Chrome with the current profile
                chrome_process = open_chrome_with_profile(google_profile)
                time.sleep(5)  # Allow Chrome to start properly

                # Simulate entering the wallet password
                locate_and_click('backpack_icon.png', confidence=0.8)
                enter_password(wallet_password)

                # Perform check-in if required
                if enable_checkin:
                    print("Check-in enabled. Performing check-in...")
                    run_checkin()
                    print(f"Check-in completed for Profile {idx + 1}.")

                # Perform transactions if required
                if enable_transactions and num_transactions > 0:
                    print(f"Starting {num_transactions} transactions for Profile {idx + 1}...")
                    repeat_transaction(num_transactions)
                    claim_box()
                    print(f"{num_transactions} transactions completed for Profile {idx + 1}.")

                # Open boxes if required
                if enable_open_box:
                    print("Opening boxes...")
                    open_box()
                    print("Box opening completed.")

            except Exception as e:
                print(f"Error processing Profile {idx + 1}: {e}")
                continue  # Skip to the next profile in case of an error

            finally:
                # Ensure Chrome is closed for the current profile
                if chrome_process:
                    close_chrome(chrome_process)
                print(f"\n--- Finished Profile {idx + 1} ---")

        print("\nAll profiles processed successfully!")

# Close the window once the loop exits
window.close()






