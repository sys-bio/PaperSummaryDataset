from src.utils import llm_caller_base


class SummaryGenerator(llm_caller_base.LLMCallerBase):

    def __init__(self):
        super().__init__()

    def generate(self, paper_file, feedback=""):
        return "# Paper summary \n\n" + self._get_paper_summary(paper_file, feedback)
        #need to put entire code here, cannot reference other modules

    def _get_paper_summary(self, paper_file, feedback=""):
        paper_summary = "## This is the summary of " + paper_file + " paper \n\n"
        # todo create the summary of the paper and concatenate it to the paper_summary. Make use of the last round feedback if available
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        return paper_summary
