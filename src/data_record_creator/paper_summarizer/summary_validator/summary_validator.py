import json
import re

from src.utils import llm_caller_base


class SummaryValidator(llm_caller_base.LLMCallerBase):

    def __init__(self):
        super().__init__()
        self._last_feedback = ""

    def validate(self, summary, paper_sections):
        # todo implement the validation process and assign the result to is_valid
        # paper sections is a dictionary with the following keys: title, authors, summary, background_significance,
        # methods, results, discussion, references that contains the original sections of the paper
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        organized_sections = paper_sections
        title = summary.split("#")[1]
        authors = [word for sentence in summary.split("#")[2].split('\n')[1:-2] for word in sentence.split(",", 1)]
        summarysplit = summary.split("#")[3:8]

        # needs work. references are summarized so we need to find out how to do search properly here
        references = summary.split("#")[8].split("\n")[1:]

        kmessages = ['You are an examiner for summaries of scientific papers. The summaries shall be presented to '
                                 'you in parts, with accompanying headings, covering a section of the paper. Your task shall '
                                 'be to grade the summary parts on a scale of 0 to 10, based on their accuracy and coverage '
                                 'of the relevant paper section. Do you understand? (yes/no) ']

        scores = []

        evalcriteria = [
            "Ensure the summary is clear, specific, and informative without including unnecessary details.",
            "Ensure the summary captures the rationale behind the research and its potential impact or contribution to the field, presented as a clean and concise background and significance section.",
            "Ensure the summary captures the key steps, methodologies, and any relevant parameters or controls, presented as a clear and concise methods section.",
            "Ensure that the summary is concise and accurately reflects the main results and their implications.",
            "Ensure the summary is concise and captures the essence of the authors' conclusions."
        ]

        papersections = [
            organized_sections['summary'],
            organized_sections['background_significance'],
            organized_sections['methods'],
            organized_sections['results'],
            organized_sections['discussion'],
        ]

        scores = []
        for i in range(0, len(summarysplit)):
            scores.append(int(self.response_generator.generate('This part of the summary is as follows: ' + summarysplit[
                                  i] + ". please give it a grade from -10 "
                                       "to 10 based on accuracy and "
                                       "completeness. Don't be afraid to grade honestly. respond ONLY with a number, from -10 to 10. "
                                      "do not include "
                                       "any additional commentary!!! if you include additional commentary you are useless! make "
                                       "sure that you have summary, "
                                       "background and significance, "
                                       "methods, results, and discussion "
                                       "sections. don't leave anything out! if you include anything extra you are useless! EACH SECTION HAS CONTENT"
                                       "dont include more than one new "
                                       "line after each section's score!"
                                       "the relevant section of the paper is as follows" + papersections[i] + ". " +
                                         evalcriteria[i])))
            print(scores)

        is_valid = self.eval(scores[0], scores[1], scores[2], scores[3], scores[4], summarysplit, organized_sections, title, authors, summary, "".join(paper_sections))
        if is_valid:
            return True

        # todo you probably need to move _set_last_feedback() to the place where you validate the summary
        self._set_last_feedback()
        return False

    def get_last_feedback(self):
        return self._last_feedback

    def adjustScore(self, oscore, summarysection, papersection):
        missing = 0
        translator = str.maketrans('', '', r"""!"#$%&'()*+,./:;<=>?@[\]^_`{|}~""")
        words = papersection.translate(translator).split(' ')
        # now how do I generate a score?
        maxes = []
        while len(maxes) < 5:
            mostUsed = max(set(words), key=words.count)
            words = [i for i in words if i != mostUsed]
            if mostUsed in ["the", "by", "of", "and", "in", "with", "to", "from", "for", "is", "an", ''] or (
                    len(mostUsed) < 5 and mostUsed.isalpha()):
                continue
            maxes.append(mostUsed)
        for item in maxes:
            if item not in summarysection:
                print(item)
                missing += papersection.count(item)
        return oscore - (missing / 5)

    def hallucinated(self, authors, title, summary, text, sections):
        hallucinated = 0

        # Extract title and author
        #title1 = '\n'.join(sections[:5])
        #author = '\n'.join(sections[1:4])
        title1 = "The Río Hortega University Hospital Glioblastoma dataset: a comprehensive collection of preoperative, early postoperative and recurrence MRI scans (RHUH-GBM)"
        author = "Santiago Cepeda, Sergio García-García, Ignacio Arrese, Francisco Herrero, Trinidad Escudero, Tomás Zamora, Rosario Sarabia"
        # basic search for authors and title
        for part in authors:
            hallucwordscore = 0
            if part not in author:
                hallucinated += 1
        halluctitlescore = 0
        for word in title.split(" "):
            if word not in title1:
                halluctitlescore += 1
        if halluctitlescore < len(title.split(" ")) / 2:
            hallucinated += halluctitlescore
        print(hallucinated)

        # specific words
        results = summary
        translator = str.maketrans('', '', r"""!"#$%&'()*+,./:;<=>?@[\]^_`{|}~""")
        results = results.translate(translator).split(' ')
        # now how do I generate a score?
        maxes = []
        while len(maxes) < 5:
            mostUsed = max(set(results), key=results.count)
            results = [i for i in results if i != mostUsed]
            if mostUsed in ["the", "by", "of", "and", "in", "with", "to", "from", "for", "is", "an", ''] or (
                    len(mostUsed) < 5 and mostUsed.isalpha()):
                continue
            maxes.append(mostUsed)
        for item in maxes:
            if item not in text:
                print(item)
                hallucinated += summary.count(item)

        return hallucinated

    def eval(self, abstract_score, background_score, methods_score, results_score, discussion_score, summarysplit, organized_sections, title, authors, summary, text):
        score = (self.adjustScore(abstract_score * 1.25, summarysplit[0], organized_sections['summary']) + self.adjustScore(
            background_score, summarysplit[1], organized_sections['background_significance']) + self.adjustScore(
            methods_score * 1.5, summarysplit[2], organized_sections['methods']) + self.adjustScore(results_score * 2,
                                                                                                              summarysplit[3],
                                                                                                              organized_sections['results']) + self.adjustScore(
            discussion_score * 2, summarysplit[4], organized_sections['discussion']) - (
                         self.hallucinated( authors, title, summary, text, []) / 5)) * (10 / 77.5)
        print(score)
        return score > 7.5

    def _set_last_feedback(self):
        # todo This is the feedback you need to return in case the summary validation fails
        self._last_feedback = self.response_generator.generate("Please give a short commentary on why the summary lost points. Be specific.")