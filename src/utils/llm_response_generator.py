import ollama

class LLMResponseGenerator:
    def __init__(self, model="llama3.1", stream=False):
        self._model = model
        self._stream = stream
        self._seed = 42
        self._temperature = 0

    def generate(self, prompt):
        return ollama.generate(model=self._model, prompt=prompt, options={"seed": self._seed, "temperature": self._temperature, "stream": self._stream})['response']