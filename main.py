import time
import random
from fixed_list import fixed_list
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
import os

from wordle_functions import analyse_guess, filter_list, send_email_result, best_next_word

# --- Configuration ---
WORDLE_PAGE = "https://www.nytimes.com/games/wordle/index.html"
MY_EMAIL = os.environ["MY_EMAIL"]
PASSWORD = os.environ["PASSWORD"]
TARGET_EMAIL = os.environ["TARGET_EMAIL"]

# --- WebDriver Setup ---
options = Options()
options.add_argument("-private")
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)
try:
    driver.get(WORDLE_PAGE)

except Exception as e:
    print(f"An error occurred: {e}")

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

time.sleep(2.0)
# --- Global Variables for the Game State ---
word_list = fixed_list
solution = [None,None,None,None,None]
absent_letters = set()
present_letters = {}
word = "canoe"
row = 1
# --- Main Game Loop ---
while True:
    time.sleep(1.5)
    rows = driver.find_element(By.CSS_SELECTOR, f'div[aria-label="Row {row}"]')
    tiles = rows.find_elements(By.XPATH, './/div[@data-testid="tile"]')

    body = driver.find_element(By.TAG_NAME, "body")
    body.send_keys(word)

    enter_button = driver.find_element(By.XPATH, "//button[@type='button' and @data-key='↵' and @aria-label='enter']")
    enter_button.click()

    time.sleep(2.5)
    # --- Call the imported functions ---
    analyse_guess(tiles, solution, present_letters, absent_letters)

    if not any(elem is None for elem in solution):
        send_email_result(game_won=True, final_word=word)
        break

    word_list = filter_list(word_list, solution, present_letters, absent_letters)

    word = best_next_word(word_list)
    if not word_list or row == 6:
        send_email_result(game_won=False, final_word=None)
        break
    row += 1

driver.quit()