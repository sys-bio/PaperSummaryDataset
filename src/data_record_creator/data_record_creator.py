from src.data_record_creator.paper_summarizer import paper_summarizer

import os


class DataRecordCreator:

    def __init__(self):
        self.paper_summarizer = paper_summarizer.PaperSummarizer()

    def create(self, models_directory):
        if not os.path.isdir(models_directory):
            raise ValueError(f"The directory {models_directory} does not exist")
        if not os.listdir(models_directory):
            raise ValueError(f"The directory {models_directory} is empty")

        for model_directory_name in os.listdir(models_directory):
            model_in_natural_language = self._create_data_record(models_directory + "/" + model_directory_name)
            if model_in_natural_language:
                self.save(model_directory_name, model_in_natural_language)

    def _create_data_record(self, model_directory):
        return self._summarize_paper(model_directory)

    def _summarize_paper(self, model_directory):
        if self._contains_paper(model_directory):
            paper_file = self._get_paper_file(model_directory)
            return self.paper_summarizer.summarize(paper_file)

        raise ValueError(f"No paper found in the model directory {model_directory}")

    @staticmethod
    def _contains_paper(model_directory):
        files = os.listdir(model_directory)
        pdf_count = sum(1 for file in files if file.lower().endswith('.pdf'))

        return pdf_count == 1

    @staticmethod
    def _get_paper_file(model_directory):
        files = os.listdir(model_directory)
        for file in files:
            if file.lower().endswith('.pdf'):
                return model_directory + "/" + file

        return None

    @staticmethod
    def save(model, model_in_natural_language):
        output_directory = "output"
        if not os.path.isdir(output_directory):
            os.mkdir(output_directory)
        with open(f"{output_directory}/{model}.txt", "w") as file:
            file.write(model_in_natural_language)



