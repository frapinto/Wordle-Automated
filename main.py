import random
import time
from collections import Counter
from fixed_list import fixed_list
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import smtplib, ssl
from email.message import EmailMessage
import os

# --- Configuration ---
WORDLE_PAGE = "https://www.nytimes.com/games/wordle/index.html"
MY_EMAIL = os.environ["MY_EMAIL"]
PASSWORD = os.environ["PASSWORD"]

chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_experimental_option("detach", True)
driver = webdriver.Chrome(options=chrome_options)

driver.get(WORDLE_PAGE)

time.sleep(4.0)

try:

    play_button = driver.find_element(By.CSS_SELECTOR, '[data-testid="Play"]')
    play_button.click()

    time.sleep(random.uniform(1, 3))

    close_icon = driver.find_element(By.XPATH, '//*[@data-testid="icon-close"]')
    close_icon.click()
    time.sleep(random.uniform(1, 5))

except Exception as e:
    print(f"An error occurred: {e}")

# --- Functions ---
def analyse_guess(tile_elements):
    count = 0
    for tile in tile_elements:

        data_state_value = tile.get_attribute("data-state") # Get the color
        tile_text = tile.text.upper() # Get the letter

        # If the letter is correct, mark its position to search
        if data_state_value == "correct":
            solution[count] = tile_text

        # If the letter is present, add it to the list and mark its position to avoid
        elif data_state_value == "present":
            if tile_text in present_letters:
                present_letters[tile_text].append(count)
            else:
                present_letters[tile_text] = [count]

        # If the letter is absent:
        elif data_state_value == "absent":
            # Check if it is already in the correct position already or (if duplicate letters) its already marked as present
            if tile_text in present_letters or tile_text in solution:
                if tile_text in present_letters:
                    present_letters[tile_text].append(count)
                else:
                    present_letters[tile_text] = [count]
            else:
                absent_letters.add(tile_text)
        count += 1


def filter_list(word_list_to_filter):
    # Filters List removing Words:
    return list(filter(lambda word: not any(char in absent_letters for char in word) # 1- With Absent letters
                                    and all(char is None or word[i] == char for i, char in enumerate(solution))
                                    # 2- Without Correct letters or in the wrong position
                                    and all(char in word and all(word[pos] != char for pos in forbidden_positions)
                                            for char, forbidden_positions in present_letters.items()), word_list_to_filter))
                                    # 3- With Present letters but in the wrong position

#Check if the game is won and send a confirmation email in said case
def send_email_result(game_won, final_word):
    msg = EmailMessage()
    msg['Subject'] = 'Wordle Result'
    msg['From'] = MY_EMAIL
    msg['To'] = "pintofrancisco97@gmail.com"

    if game_won:
        msg.set_content(f"You won today's Wordle!\n\nCongratulations, the word today was {final_word}!")
    else:
        msg.set_content("You lost today's Wordle.\n\nSomething went wrong or there was a game update.")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as connection:
            connection.login(MY_EMAIL, PASSWORD)
            connection.send_message(msg)
        print("Email sent successfully!")
    except smtplib.SMTPAuthenticationError:
        print("Failed to log in. Check your email and password.")
    except Exception as e:
        print(f"An error occurred while sending the email: {e}")

# Choose the best next word with distinct letters or if it is impossible, returns first word
def best_next_word(words):
    for word in words:
        freq = Counter(word)
        if (len(freq) == len(word)):
            return word
    return words[0]

# Use Wordle word database
word_list = fixed_list
solution = [None,None,None,None,None]
absent_letters = set()
present_letters = {}
word = "canoe" # Just can't beat the best word
row = 1
while True:
    time.sleep(1.5)
    # Select Tiles in present row
    rows = driver.find_element(By.CSS_SELECTOR, f'div[aria-label="Row {row}"]')
    tiles = rows.find_elements(By.XPATH, './/div[@data-testid="tile"]')

    # Input selected word letters
    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(word)

    # Click and Wait
    enter_button = driver.find_element(By.XPATH, "//button[@type='button' and @data-key='↵' and @aria-label='enter']")
    enter_button.click()

    # Analyze the result and save correct and present letters
    time.sleep(2.5)
    analyse_guess(tiles)

    # If solution is filled, end the game
    if not any(elem is None for elem in solution):
        send_email_result(game_won = True, final_word = word)
        break

    # Filter the list
    word_list = filter_list(word_list)

    # Select a random new word from the modified list and go to the next row
    word = best_next_word(word_list)
    if not word_list or row == 6:
        send_email_result(game_won = False, final_word = None)
        break
    row += 1