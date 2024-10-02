from src.utils import llm_caller_base


class SummaryValidator(llm_caller_base.LLMCallerBase):

    def __init__(self):
        super().__init__()
        self._last_feedback = ""

    def validate(self, summary, paper_file):
        # todo implement the validation process and assign the result to is_valid
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        title = summary.split("#")[1]
        authors = [word for sentence in summary.split("#")[2].split('\n')[1:-2] for word in sentence.split(",", 1)]
        summarysplit = summary.split("#")[3:8]

        # needs work. references are summarized so we need to find out how to do search properly here
        references = summary.split("#")[8].split("\n")[1:]

        is_valid = True
        if is_valid:
            return True

        # todo you probably need to move _set_last_feedback() to the place where you validate the summary
        self._set_last_feedback()
        return False

    def get_last_feedback(self):
        return self._last_feedback

    def _set_last_feedback(self):
        # todo This is the feedback you need to return in case the summary validation fails
        self._last_feedback = self.response_generator.generate("Please give a short commentary on why the summary lost points. Be specific.")