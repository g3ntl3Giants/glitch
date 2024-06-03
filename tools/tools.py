from openai import OpenAI

def create_documentation(client: OpenAI, code: str) -> str:
    prompt = f"Create documentation for the following code:\n\n{code}\n\nDocumentation:"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}]
    )
    documentation = response.choices[0].message.content
    return documentation

def create_unit_tests(client: OpenAI, code: str) -> str:
    prompt = f"Create unit tests for the following code:\n\n{code}\n\nUnit Tests:"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": prompt}]
    )
    unit_tests = response.choices[0].message.content
    return unit_tests


tools = [
    {
        "type": "function",
        "function": {
            "name": "create_documentation",
            "description": "Create documentation for the provided code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_unit_tests",
            "description": "Create unit tests for the provided code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            }
        }
    }
]
