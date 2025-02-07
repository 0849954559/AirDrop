import PySimpleGUI as sg
import subprocess
import pyautogui
import time
import json
import os

# JSON file to store the entry data
data_file = 'profiles.json'


# Function to create the main layout
def create_layout():
    """Generates the layout for the entry form."""
    layout = [
        [sg.Text('Tool Airdrop', font=('Arial', 14, 'bold'))],
        [sg.Text('Google Profile', size=(15, 1)), sg.InputText(key='Google Profile')],
        [sg.Text('Crypto Wallet Password', size=(15, 1)),
         sg.InputText(key='Crypto Wallet Password', password_char='*')],
        [sg.Button('Open Profile'), sg.Exit()]
    ]
    return layout


def open_chrome_with_profile(profile_name):
    """Open Chrome with a specified user profile without showing a popup."""
    chrome_path = os.path.join(os.getenv('LOCALAPPDATA'), r'Google\Chrome\Application\chrome.exe')
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

    if not os.path.exists(chrome_path):
        sg.popup_error("Chrome executable not found! Please check your installation.")
        return

    subprocess.Popen([
        chrome_path,
        f'--profile-directory={profile_name}',
        '--new-window',
        '--start-maximized',
        'https://www.google.com'
    ])



def get_icon_path():
    """Get the path of the backpack_icon.png inside the 'images' folder relative to the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get script directory
    icon_path = os.path.join(script_dir, "images","sonic", "backpack_icon.png")  # Look in 'images' folder
    return icon_path


def click_extension():
    """Locate and click the pinned Chrome extension with smooth mouse movement."""
    time.sleep(3)  # Give Chrome extra time to load
    print("Locating the Backpack Wallet extension...")

    icon_path = get_icon_path()  # Get the correct icon path dynamically

    # Check if the file exists before using it
    if not os.path.exists(icon_path):
        sg.popup_error(f"Error: The icon file was not found at:\n{icon_path}\nPlease ensure it's in the same folder as the script.")
        return

    location = None
    for _ in range(5):  # Try locating the icon multiple times
        location = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
        if location:
            break
        time.sleep(1)

    if location:
        x, y = location
        pyautogui.moveTo(x, y, duration=1.5)  # Smoothly move the cursor over 1.5 seconds
        pyautogui.click()
        print("Backpack Wallet extension clicked.")
    else:
        sg.popup_error("Could not find the Backpack Wallet extension. Ensure it's visible on the screen.")
def enter_password(password):
    """Simulate human-like password entry."""
    time.sleep(5)  # Wait for Chrome to fully load
    pyautogui.typewrite(password, interval=0.15)  # Simulate typing
    pyautogui.press('enter')

# Load previous data if exists
try:
    with open(data_file, 'r') as file:
        profiles_data = json.load(file)
except FileNotFoundError:
    profiles_data = []

# Create the window
window = sg.Window('Dynamic Entry Form', create_layout(), finalize=True)

while True:
    event, values = window.read()

    if event in (sg.WIN_CLOSED, 'Exit'):
        break

    if event == 'Open Profile':
        google_profile = values['Google Profile']
        wallet_password = values['Crypto Wallet Password']

        if not google_profile or not wallet_password:
            sg.popup("Please enter both the Google Profile and Wallet Password.")
            continue

        # Save the data to JSON
        entry = {"Chrome Profile": google_profile, "Crypto Wallet Password": wallet_password}
        profiles_data.append(entry)
        with open(data_file, 'w') as file:
            json.dump(profiles_data, file, indent=4)

        # Open Chrome and handle automation

        open_chrome_with_profile(google_profile)
        time.sleep(2)  # Wait for Chrome to launch
        click_extension()  # Click on the extension icon
        enter_password(wallet_password)  # Enter the password

window.close()
