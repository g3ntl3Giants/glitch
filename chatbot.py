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
from data_processing import extract_text_from_html, extract_text_from_pdf, extract_text_from_txt, _extract_text
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

# Initialize the chatbot class
chatbot_instance = None

def process_file(file_path):
    file_name = os.path.basename(file_path)
    file_contents = _extract_text(file_name, file_path)
    return "\n" + file_contents[1] if file_contents[1] else ""

def setup_chatbot():
    global chatbot_instance
    try:
        # Start timer to calculate setup time
        start_time = time.time()
        print('\nStarting bot setup...\n')
        logging.info('Starting bot setup...')

        # Initialize the chatbot class
        chatbot_instance = ChatGPT(OPENAI_API_KEY, CHATBOT_SYSTEM_MESSAGE)

        # Calculate and print setup time
        setup_time = (time.time() - start_time)
        print(f"Chatbot setup completed in {setup_time:.2f} seconds.")
        logging.info(f'Chatbot setup completed in {setup_time:.2f} seconds.')
    except Exception as e:
        logging.error(f"Error in setup_chatbot: {e}")
        print(f"Error: {e}")

def chat_with_user(user_input):
    try:
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
                    return {"error": f"The path does not exist: {file_path}"}

            if combined_file_contents:
                response = chatbot_instance.chat(combined_file_contents, LOG_FILE, BOT_NAME)
                return {"response": response}
            else:
                return {"error": "No valid files or directories were provided."}
        else:
            response = chatbot_instance.chat(user_input, LOG_FILE, BOT_NAME)
            return {"response": response}
    except Exception as e:
        logging.error(f"Error in chat_with_user: {e}")
        return {"error": str(e)}

# Call setup_chatbot on import
setup_chatbot()
