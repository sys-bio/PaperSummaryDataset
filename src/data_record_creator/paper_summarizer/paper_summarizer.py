import json

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
        with open("/home/epshtein/Documents/GitHub/PaperSummaryDataset/test/models/model/combined_sections.json", "r") as file:
            dict = json.loads(file.read())
        summary = {
            "title": dict["title"]["summary"],
            "authors": dict["authors"]["summary"],
            "background": dict["background_significance"]["summary"],
            "summary": dict["summary"]["summary"],
            "results": dict["results"]["summary"],
            "methods": dict["methods"]["summary"],
            "discussion": dict["discussion"]["summary"],
            "references": dict["results"]["summary"]
        }
            #self.summarizer.generate(paper_file=paper_file, feedback=feedback)
        paper_sections ={
            "title": dict["title"]["section"],
            "authors": dict["authors"]["section"],
            "background_significance": dict["background_significance"]["section"],
            "results": dict["results"]["section"],
            "summary": dict["summary"]["section"],
            "methods": dict["methods"]["section"],
            "discussion": dict["discussion"]["section"],
            "references": dict["results"]["section"]
        }
            #self.summarizer.get_paper_sections()
        if self.summary_validator.validate(summary, paper_sections):
            return summary
        else:
            self.max_num_of_tries += 1
            if self.max_num_of_tries < 5:
                print(self.summary_validator.get_last_feedback())
                self._get_paper_summary(paper_file, self.summary_validator.get_last_feedback())


        return ""


PaperSummarizer()._get_paper_summary(paper_file="/home/epshtein/Documents/GitHub/PaperSummaryDataset/src/paper.pdf")