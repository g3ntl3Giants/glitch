# chatbot.py

import os
import json
import logging
import time
import threading
from openai import OpenAI
from pathlib import Path
from chatgpt import ChatGPT
from cli_animations import loading_animation
from data_processing import extract_text_from_html, extract_text_from_pdf, extract_text_from_txt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(filename="chatbot.log", level=logging.INFO)

# Define constants
BOT_NAME = "Glitch"
LOG_FILE = "chat_log.txt"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHATBOT_SYSTEM_MESSAGE = extract_text_from_txt('./sys_prompt.md')


def process_file(file_path):
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    file_contents = ""
    # Process known file types
    if file_extension in ['.pdf', '.txt', '.html']:
        if file_extension == '.pdf':
            file_contents = extract_text_from_pdf(file_path)
        elif file_extension == '.txt':
            file_contents = extract_text_from_txt(file_path)
        elif file_extension == '.html':
            file_contents = extract_text_from_html(file_path)
    elif file_extension in ['.py', '.tsx', '.jsx', '.js', '.ts']:
        file_contents = extract_text_from_txt(file_path)
    elif file_extension == '.json':
        with open(file_path, 'r', encoding='utf-8') as file:
            file_contents = json.dumps(json.load(file), indent=2)
    else:
        print(f"{BOT_NAME}: I'm sorry, I can't process the file: {file_path}")
        return ""
    return "\n" + file_contents


def setup_chatbot():
    try:
        # Start the loading animation in a separate thread
        stop_animation = threading.Event()
        animation_thread = threading.Thread(
            target=loading_animation, args=(stop_animation,))
        animation_thread.start()

        # Start timer to calculate setup time
        start_time = time.time()
        print('\nStarting bot setup...\n')
        logging.info('Starting bot setup...')

        # Initialize the chatbot class
        global chatbot_instance
        chatbot_instance = ChatGPT(OPENAI_API_KEY, CHATBOT_SYSTEM_MESSAGE)

        # Stop the loading animation
        stop_animation.set()
        animation_thread.join()

        # Calculate and print setup time
        setup_time = (time.time() - start_time)
        print(f"Chatbot setup completed in {setup_time:.2f} seconds.")
        logging.info(f'Chatbot setup completed in {setup_time:.2f} seconds.')
    except Exception as e:
        logging.error(f"Error in setup_chatbot: {e}")
        print(f"Error: {e}")


def chat_with_user():
    try:
        print(f"{BOT_NAME}: Hi! How can I assist you today?")
        logging.info('Entering chat_with_user function.')

        while True:
            user_input = input("You: ").strip()

            # Exit condition
            if user_input.lower() in ["exit", "quit", "bye"]:
                print(f"{BOT_NAME}: Goodbye! Have a great day.")
                break

            # Check for the 'files:' keyword in the input
            if 'files:' in user_input:
                _, file_list = user_input.split('files:', 1)
                file_paths = file_list.split(',')

                combined_file_contents = ""
                for file_path_str in file_paths:
                    file_path = Path(file_path_str.strip())
                    if file_path.is_file():
                        combined_file_contents += process_file(file_path)
                    elif file_path.is_dir():
                        for child in file_path.glob('**/*'):
                            if child.is_file():
                                combined_file_contents += process_file(child)
                    else:
                        print(f"{BOT_NAME}: The path does not exist: {file_path}")
                        continue

                if combined_file_contents:
                    response = chatbot_instance.chat(
                        combined_file_contents, LOG_FILE, BOT_NAME)
                    print(f"{BOT_NAME}: {response}")
                else:
                    print(
                        f"{BOT_NAME}: No valid files or directories were provided.")
            else:
                response = chatbot_instance.chat(
                    user_input, LOG_FILE, BOT_NAME)
                print(f"{BOT_NAME}: {response}")

    except Exception as e:
        logging.error(f"Error in chat_with_user: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        setup_chatbot()
        chat_with_user()
    except Exception as e:
        logging.error(f"Error in main: {e}")
        print(f"Error: {e}")
