from src.data_record_creator.paper_summarizer.summary_generator import summary_generator
from src.data_record_creator.paper_summarizer.summary_validator import summary_validator


class PaperSummarizer:

    def __init__(self):
        self.summarizer = summary_generator.SummaryGenerator()
        self.summary_validator = summary_validator.SummaryValidator()
        self.max_num_of_tries = 0

    def summarize(self, paper_file):
        return self._get_paper_summary(paper_file)

    def _get_paper_summary(self, paper_file, feedback=""):
        summary = self.summarizer.generate(paper_file, feedback)
        if self.summary_validator.validate(summary, paper_file):
            return summary
        else:
            self.max_num_of_tries += 1
            if self.max_num_of_tries < 5:
                self._get_paper_summary(paper_file, self.summary_validator.get_last_feedback())


        return ""