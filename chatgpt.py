# chatgpt.py
import openai
from openai import OpenAI
import time
import logging
from typing import List, Optional, Dict, Any

# Define an exception for the ChatGPT class for better error handling.


class ChatGPTError(Exception):
    pass


class ChatGPT:
    DEFAULT_PARAMS: Dict[str, Any] = {
        "temperature": 0.75,
        "frequency_penalty": 0.2,
        "presence_penalty": 0
    }

    def __init__(self, api_key: str, chatbot: str, retries: int = 3):
        self.api_key = api_key
        self.chatbot = chatbot
        self.conversation: List[Dict[str, str]] = []
        self.retries = retries
        self.client = OpenAI(api_key=self.api_key)

    def chat(self, user_input, log_file, bot_name):
        self.conversation.append({"role": "user", "content": user_input})

        response = self.chatgpt_with_retry(
            self.conversation, self.chatbot, user_input,)

        self.conversation.append({"role": "assistant", "content": response})
        # Save to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"User: {user_input}\n")
            f.write(f"{bot_name}: {response}\n\n")
        # Remove 3rd oldest message from the conversation after 4 turns
        if len(self.conversation) > 4:
            self.conversation.pop(2)
        return response

    def chatgpt(self, conversation: List[Dict[str, str]], chatbot: str, **kwargs) -> str:
        params = {**self.DEFAULT_PARAMS, **kwargs}

        messages_input = conversation.copy()

        prompt = [{"role": "system", "content": chatbot}]

        messages_input.insert(0, prompt[0])

        completion = self.client.chat.completions.create(model="gpt-4-0125-preview",
                                                         temperature=params["temperature"],
                                                         frequency_penalty=params["frequency_penalty"],
                                                         presence_penalty=params["presence_penalty"],
                                                         messages=messages_input)

        chat_response = completion.choices[0].message.content
        return chat_response

    def chatgpt_with_retry(self, conversation, chatbot, user_input, **kwargs):
        response = None
        backoff_factor = 1.5
        wait_time = 0.1

        for i in range(self.retries):
            try:

                response = self.chatgpt(
                    conversation, chatbot, user_input, **kwargs)

                return response
            except openai.RateLimitError as e:
                logging.warning(f"Rate limit reached, waiting for {
                                wait_time} seconds before retrying...")
                print(f"Rate limit reached, waiting for {
                      wait_time} seconds before retrying...")
                time.sleep(wait_time)
                wait_time *= backoff_factor
            except openai.APIStatusError as e:
                logging.warning(f"Error in chatgpt attempt {
                                i + 1}: {e}. Retrying...")
            except Exception as e:
                logging.error(f"Unexpected error in chatgpt attempt {
                              i + 1}: {e}. No more retries.")
                raise ChatGPTError from e
        return None
