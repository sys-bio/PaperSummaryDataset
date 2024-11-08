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
        title = summary["title"]
        authors = [word for sentence in summary["authors"].split('\n')[1:-2] for word in sentence.split(",", 1)]
        summarysplit = [
            summary["summary"],
            summary["background"],
            summary["methods"],
            summary["results"],
            summary["discussion"],
        ]

        # needs work. references are summarized so we need to find out how to do search properly here
        references = summary['references']

        self.response_generator.generate('You are an examiner for summaries of scientific papers. The summaries shall be presented to '
                                                     'you in parts, with accompanying headings, covering a section of the paper. Your task shall '
                                                     'be to grade the summary parts on a scale of 0 to 10, based on their accuracy and coverage '
                                                     'of the relevant paper section. Do you understand? (yes/no) ')
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
                         "to 10 based on accuracy and completeness."
                         "the relevant section of the paper is as follows" + papersections[i] + ". " +
                                            evalcriteria[i] + "REPLY ONLY WITH ONE INTEGER VALUE BETWEEN -10 AND 10. NO TEXT.")))

        is_valid = self.eval(scores[0], scores[1], scores[2], scores[3], scores[4], summarysplit, organized_sections,
                             title, authors, summary, "".join(paper_sections))
        print(scores)
        if is_valid > 7.5:
            return True

        # todo you probably need to move _set_last_feedback() to the place where you validate the summary
        self._set_last_feedback(''.join(x for x in summary.values()),  "".join(paper_sections), is_valid)
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
                missing += papersection.count(item)
        return oscore - (missing / 5)

    def hallucinated(self, authors, title, summarytext, text):
        hallucinated = 0

        # basic search for authors and title
        for part in authors:
            hallucwordscore = 0
            if part not in text:
                hallucinated += 1
        halluctitlescore = 0
        for word in title.split(" "):
            if word not in text:
                halluctitlescore += 1
        if halluctitlescore < len(title.split(" ")) / 2:
            hallucinated += halluctitlescore

        # specific words
        results = summarytext
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
                hallucinated += summarytext.count(item)

        return hallucinated

    def eval(self, abstract_score, background_score, methods_score, results_score, discussion_score, summarysplit,
             organized_sections, title, authors, summary, text):
        score = ((abstract_score * 1.25) + self.adjustScore(
            background_score, summarysplit[1], organized_sections['background_significance']) + self.adjustScore(
            methods_score * 1.5, summarysplit[2], organized_sections['methods']) + self.adjustScore(results_score * 2,
                                                                                                    summarysplit[3],
                                                                                                    organized_sections[
                                                                                                        'results']) + self.adjustScore(
            discussion_score * 2, summarysplit[4], organized_sections['discussion']) - (
                         self.hallucinated(authors, title, ''.join(x for x in summary.values()), text) / 5)) * (10 / 77.5)
        print(score)
        return score

    def _set_last_feedback(self, summary_text, text, points):
        # todo This is the feedback you need to return in case the summary validation fails

        self._last_feedback = self.response_generator.generate("You are an examiner for summaries of scientific papers. You have been presented with the following summary:" + summary_text + ", which is a summary of the following paper:"
                                                               + text + "it received " + points.__str__() + "points, under the threshhold of 7.5 required to pass. Please give a short commentary on why the summary lost points. Be specific.")
