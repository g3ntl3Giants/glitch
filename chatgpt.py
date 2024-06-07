import openai
from openai import OpenAI
import logging
from typing import List, Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_random_exponential
import tiktoken
import json
from tools.tools import create_documentation, create_unit_tests, save_documents, tools

class ChatGPTError(Exception):
    pass

class ChatGPT:
    DEFAULT_PARAMS: Dict[str, Any] = {
        "temperature": 0.75,
        "frequency_penalty": 0.2,
        "presence_penalty": 0
    }
    MAX_TOKENS: int = 64000

    def __init__(self, api_key: str, chatbot: str):
        self.api_key = api_key
        self.chatbot = chatbot
        self.client = OpenAI(api_key=self.api_key)
        self.conversation: List[Dict[str, str]] = [
            {"role": "system", "content": chatbot}]
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.tools = tools

    def trim_conversation_to_fit_token_limit(self, conversation, max_tokens=128000):
        encoded_convo = [self.encoder.encode(
            msg["content"]) for msg in conversation]
        total_tokens = sum(len(tokens) for tokens in encoded_convo)

        # Trim from the start until we are under the max token limit
        # Keep at least the last message and system prompt
        while total_tokens > max_tokens and len(conversation) > 2:
            # Remove the earliest user or bot message
            removed_message = conversation.pop(1)
            removed_tokens = len(self.encoder.encode(
                removed_message["content"]))
            total_tokens -= removed_tokens

        return conversation

    def chat(self, user_input: str, log_file: str, bot_name: str) -> str:
        # Tokenize the user input
        tokenized_input = self.encoder.encode(user_input)

        # Calculate how many chunks are needed
        chunks = [tokenized_input[i:i + self.MAX_TOKENS]
                  for i in range(0, len(tokenized_input), self.MAX_TOKENS)]

        # Process each chunk
        full_response = self.process_chunks(chunks, log_file, bot_name)

        return full_response

    # Correct the return type of the chatgpt method
    def chatgpt(self, conversation: List[Dict[str, str]], **kwargs) -> Any:
        params = {**self.DEFAULT_PARAMS, **kwargs}
        messages_input = conversation.copy()

        if self.tools:
            logging.info(f'ping...{self.tools}')
            print(f'ping...{self.tools}')
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                temperature=params["temperature"],
                frequency_penalty=params["frequency_penalty"],
                presence_penalty=params["presence_penalty"],
                messages=messages_input,
                tools=self.tools,
                tool_choice="auto"
            )
        else:
            logging.info(f'ping...no tools...{self.tools}')
            print(f'ping...no tools...{self.tools}')
            completion = self.client.chat.completions.create(
                model="gpt-4o",
                temperature=params["temperature"],
                frequency_penalty=params["frequency_penalty"],
                presence_penalty=params["presence_penalty"],
                messages=messages_input
            )

        chat_response = completion.choices[0].message

        tool_calls = chat_response.tool_calls
        if tool_calls:
            available_functions = {
                "create_documentation": create_documentation,
                "create_unit_tests": create_unit_tests,
                "save_documents": save_documents
            }

            messages_input.append(chat_response)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)

                if function_name == "create_documentation":
                    function_response = function_to_call(function_args["code"])
                elif function_name == "create_unit_tests":
                    function_response = function_to_call(function_args["code"])
                elif function_name == "save_documents":
                    function_response = function_to_call(function_args["document_content"], function_args["file_name"], function_args["file_extension"])

                messages_input.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(function_response),
                })

            second_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages_input
            )

            print(f'Second message: {second_response.choices[0].message.content}')
            return second_response.choices[0].message

        return chat_response

    # Update process_chunks to handle the returned response correctly
    def process_chunks(self, chunks, log_file, bot_name):
        full_response = ""
        total_chunks = len(chunks)
        chunks_processed = 0

        for i, chunk in enumerate(chunks):
            chunk_text = self.encoder.decode(chunk)
            header = f"Chunk: {i+1} out of {total_chunks}\n"
            footer = "Please respond now, all chunks have been sent." if i == total_chunks - 1 else f"respond with an empty string until Chunk {total_chunks}"
            chunk_text = f"{header}{chunk_text}\n{footer}"
            self.conversation.append({"role": "user", "content": chunk_text})

            chunks_processed += 1
            logging.info(f"Processing chunk {chunks_processed}/{total_chunks}")
            print(f"Processing chunk {chunks_processed}/{total_chunks}...")

            response = self.chatgpt_with_retry(conversation=self.conversation)
            
            logging.info(f"response: {response}")
            print(f"response: {response}")

            response_content = response.content

            logging.info(f"response content: {response_content}")
            print(f"response content: {response_content}")

            self.conversation.append({"role": "assistant", "content": response_content})
            full_response += response_content

            logging.info(f"""Chunk {chunks_processed} processed. User: {chunk_text[:50]}... Assistant: {response_content[:50]}...""")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"User: {chunk_text}\n{bot_name}: {response_content}\n\n")

            print(f"Chunk {chunks_processed}/{total_chunks} processed.")

            if len(self.conversation) > 4:
                self.conversation.pop(2)
                self.conversation.pop(2)

        logging.info("All chunks processed successfully.")
        print("All chunks processed successfully.")

        return full_response

    @retry(wait=wait_random_exponential(multiplier=1, max=120), stop=stop_after_attempt(10), reraise=True)
    def chatgpt_with_retry(self, conversation: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None, **kwargs) -> Optional[str]:
        try:
            # Trim conversation if it exceeds the token limit
            conversation = self.trim_conversation_to_fit_token_limit(
                conversation, 128000)
            return self.chatgpt(conversation, **kwargs)
        except openai.APIStatusError as e:
            logging.error(f"Error during chat completion: {e}")
            raise ChatGPTError from e
