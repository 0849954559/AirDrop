import PySimpleGUI as sg
import pandas as pd

# Set color theme
sg.theme('DarkBlue')

# Load existing Excel file
ExcelFile = 'Data_Entry.xlsx'
df = pd.read_excel(ExcelFile)

layout = [
    [sg.Text('Tool airdrop')],
    [sg.Text('Google Profile', size=(15, 1)), sg.InputText(key='Google Profile')],
    [sg.Text('Password', size=(15, 1)), sg.InputText(key='Password')],
    [sg.Submit(), sg.Button ('clear'), sg.Exit()]
]

window = sg.Window('Simple Data Entry Form', layout)

def clear_input():
    for key in values:
        window[key]('')
    return None

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == 'Exit':
        break
    if event == 'clear':
        clear_input()
    if event == 'Submit':
        new_data = pd.DataFrame([values])  # Convert input values to DataFrame
        df = pd.concat([df, new_data], ignore_index=True)  # Corrected method
        df.to_excel(ExcelFile, index=False)  # Save changes
        sg.popup('Data saved successfully!')
        clear_input()
window.close()
