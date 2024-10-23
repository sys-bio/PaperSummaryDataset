import requests
import json
import ollama


class LLMResponseGenerator:

    def generate(self, prompt):
        response = ollama.chat(
            model='llama3.1',
            messages=[prompt],
            stream=False,
            options={"temperature": 0.0, "seed": 42}
        )
        return response
