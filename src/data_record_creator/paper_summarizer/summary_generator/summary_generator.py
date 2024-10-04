from src.utils import llm_caller_base


class SummaryGenerator(llm_caller_base.LLMCallerBase):

    def __init__(self):
        super().__init__()
        self._paper_sections = {}

    def generate(self, paper_file, feedback=""):
        self._paper_sections = self._extract_paper_sections(paper_file)
        return "# Paper summary \n\n" + self._get_paper_summary(feedback)
        #need to put entire code here, cannot reference other modules

    def get_paper_sections(self):
        return self._paper_sections

    @staticmethod
    def _extract_paper_sections(paper_file):
        # todo extract the sections of the paper and assign them to the _paper_sections attribute.
        #  We want a dictionary with the following keys (you can use the titles you are using,
        #  so these are just examples): title, authors, summary, background_significance,
        #  methods, results, discussion, references
        paper_sections = {'title': 'title', 'authors': 'authors', 'summary': 'summary',
                          'background_significance': 'background_significance', 'methods': 'methods',
                          'results': 'results', 'discussion': 'discussion', 'references': 'references'}
        return paper_sections

    def _get_paper_summary(self, feedback=""):
        paper_summary = "## This is the summary of " + self._paper_sections['title'] + " paper \n\n"
        # todo create the summary of the paper and concatenate it to the paper_summary.
        #  Make use of the last round feedback if available
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        return paper_summary
