from src.utils import llm_caller_base

class SummaryValidator(llm_caller_base.LLMCallerBase):

    def __init__(self):
        super().__init__()
        self._last_feedback = ""

    def validate(self, summary, paper_file):
        # todo implement the validation process and assign the result to is_valid
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        is_valid = False
        if is_valid:
            return True

        # todo you probably need to move _set_last_feedback() to the place where you validate the summary
        self._set_last_feedback()
        return False

    def get_last_feedback(self):
        return self._last_feedback

    def _set_last_feedback(self):
        # todo This is the feedback you need to return in case the summary validation fails
        self._last_feedback = "Your previous summary was not valid as the following issues were found: ..."