from collections import Counter
import smtplib, ssl
from email.message import EmailMessage
import os

MY_EMAIL = os.environ["MY_EMAIL"]
PASSWORD = os.environ["PASSWORD"]
TARGET_EMAIL = os.environ["TARGET_EMAIL"]

# --- Functions ---
def analyse_guess(tile_elements, solution, present_letters, absent_letters):
    count = 0
    for tile in tile_elements:
        data_state_value = tile.get_attribute("data-state")
        tile_text = tile.text.upper()

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
            # Check if it is already in the correct position
            # already or (if duplicate letters) its already marked as present
            if tile_text in present_letters or tile_text in solution:
                if tile_text in present_letters:
                    present_letters[tile_text].append(count)
                else:
                    present_letters[tile_text] = [count]
            else:
                absent_letters.add(tile_text)
        count += 1

def filter_list(word_list_to_filter, solution, present_letters, absent_letters):
    # Filters List removing Words:
    return list(filter(lambda word: not any(char in absent_letters for char in word)  # 1- With Absent letters
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
    msg['To'] = TARGET_EMAIL

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