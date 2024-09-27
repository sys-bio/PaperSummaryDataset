from src.utils.llm_response_generator import LLMResponseGenerator


class LLMCallerBase:

    def __init__(self):
        self.response_generator = LLMResponseGenerator()
