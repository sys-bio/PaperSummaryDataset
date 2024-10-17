import requests
import json


class LLMResponseGenerator:
    def __init__(self, model="llama3.1", stream=False):

        self.model = model
        self.stream = stream
        self.url = "http://localhost:11434/api/generate"
        self.headers = {"Content-Type": "application/json"}

    def generate(self, prompt):
        data = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "seed": 42,
                "temperature": 0
            },
            "stream": self.stream
        }
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data))
        if response.status_code == 200:
            response_text = response.text
            data = json.loads(response_text)
            actual_response = data["response"]
            return actual_response
        else:
            return "Error:", response.status_code, response.text
