import fitz
import re
import os 
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import tempfile 
import ollama 

class SummaryGenerator(llm_caller_base.LLMCallerBase): 
    def__init__(self): 
        super().__init__()
        self._organized_sections = {}
        self._categories = {"abstract": "", "introduction": "", "methods" : "", "results" : "", "discussion": "", "conclusion" : "", "references" : "", "title" : "", "authors" : ""}
        
    def generate(self, paper_file, feedback = ""): 
        return "# Paper summary \n\n" + self._process_files(feedback)
    
    def get_paper_sections(self): 
        return self._organized_sections
    
    def clean_text(self, text):
        cleaned_text = "\n".join([line for line in text.splitlines() if re.match(r'^[\x00-\x7F]+$', line)])
        return cleaned_text

    def extract_and_clean_pdf(self, pdf_path):
        print(f"Extracting text from PDF: {pdf_path}...")
        doc = fitz.open(pdf_path)
        pdf_text = ""

        for page in doc:
            pdf_text += page.get_text("text") + "\n"

        cleaned_text = self.clean_text(pdf_text)
        return cleaned_text
    
    def process_files(self, paper_file): 
        LOCAL_DOWNLOAD_DIR = tempfile.mkdtemp() 
        os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok = True) 
        cleaned_text = self.extract_and_clean_pdf(paper_file)
        
        lines_before_abstract, grouped_sentences = self.split_top_file(cleaned_text)
        self.split_lines_before(lines_before_abstract)
        self.split_lines_after(grouped_sentences)
        organized_sections = self.group_lines()
        self.organized_sections = organized_sections
        
        final = self.summarize_sections(organized_sections)
        return final

    def split_top_file(self, md_text):
        lines_before_abstract = []
        abstract = ""
        text_after_abstract = ""
        reached_abstract = False
        reached_introduction = False

        # Split the text into lines
        for line in md_text.splitlines():
            if ("abstract" in line.lower() or "summary" in line.lower()) and len(line.split()) == 1:  # Start capturing the abstract once "abstract" or "background" is found
                reached_abstract = True
                abstract += line + "\n"  # Add the abstract header line
                continue  # Skip the abstract header line itself

            if reached_abstract and not reached_introduction:  # Capture the abstract content until Introduction
                abstract += line + "\n"
                
            # Check for the introduction or background header as a single word
            if reached_abstract and not reached_introduction:
                line_words = line.strip().split()  # Split the line into words
                if len(line_words) == 1 and ("introduction" in line.lower() or "background" in line.lower()):
                    reached_introduction = True
                    continue  # Skip the introduction/header line (do not add to abstract)

            # Capture everything after the abstract (including introduction and beyond)
            if reached_abstract and reached_introduction:
                text_after_abstract += line + "\n"

            if not reached_abstract:
                # Collect lines before the abstract
                lines_before_abstract.append(line)

        # Split the part after the abstract into sentences for grouping
        sentences_after_abstract = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text_after_abstract.strip())
        grouped_sentences = [sentences_after_abstract[i:i + 7] for i in range(0, len(sentences_after_abstract), 7)]

        self.categories["abstract"] = abstract
        return lines_before_abstract, grouped_sentences

    def split_lines_before(self, lines_before_abstract): 
        contains_person = False
        abstract_found = False

        title = ""
        authors = "" 
        
        for _, line in enumerate(lines_before_abstract):
            tokenizer = AutoTokenizer.from_pretrained("dslim/bert-large-NER")
            model = AutoModelForTokenClassification.from_pretrained("dslim/bert-large-NER")
            nlp = pipeline("ner", model=model, tokenizer=tokenizer)
            results_for_nlp = nlp(line)
            
            for entity in results_for_nlp:
                if entity['entity'] in ["PER", "B-PER", "I-PER", "LOC", "ORG"]:
                    authors += line + "\n"
                    contains_person = True
                    break
                
            if "abstract" in line.lower(): 
                abstract_found = True
                
            if not contains_person and not abstract_found:
                title += line + "\n"
        
        self.categories["title"] = title 
        self.categories["authors"] = authors
        
    def split_lines_after(self, grouped_sentences):
        introduction = ""
        methods = ""
        results = ""
        discussion = ""
        conclusion = ""
        references = ""
        for idx, group in enumerate(grouped_sentences):
            group_text = "\n".join(group)
            print(f"Processing group {idx + 1}/{len(grouped_sentences)}: {group_text[:100]}...")

            prompt_template = f"""
            Classify the given text into one of the following sections:

            Introduction: Provides background information, outlines the research problem, or states the research objectives or hypothesis.

            Methods: Describes the procedures, techniques, materials, and methodology used to conduct the research.

            Results: Reports the raw findings from the study. This section presents data, observations, or outcomes without providing any explanations or interpretations. Results typically include specific measurements, statistical outcomes, trends, or comparisons. It focuses purely on what was observed or measured, with no discussion of why these results occurred.

            Discussion: Analyzes and interprets the findings. This section explains the significance of the results, connects them to existing research, identifies potential reasons for observed trends or discrepancies, and may include study limitations or suggestions for future research. The discussion provides context or explanations for the observed results and does not just state raw data.

            Conclusion: Summarizes the key findings, provides an answer to the research question, and highlights broader implications. This section typically begins with phrases such as "In conclusion," "To conclude," or "In summary," and may suggest future research directions or implications for practice. It does not introduce new data or results but reflects on the meaning or significance of the study as a whole.
            If the section contains "In conclusion, " return conclusion.

            References: Lists all sources cited throughout the paper.
            
            ONLY OUTPUT THE NAME OF THE SECTION. DO NOT EXPLAIN YOUR DECISION-MAKING. 
            
            Text: {group_text}
            """
            
            # Get classification from Groq API
            print(f"Sending request to Groq API for group {idx + 1}...")
            
            category = ollama.generate(model = "llama3", prompt = prompt_template)
            print(f"Groq classification for group {idx + 1}: {category['response'].strip().lower()}")

            # Categorize the group based on the response
            if "introduction" in category:
                introduction += group_text + "\n"
            elif "methods" in category:
                methods += group_text + "\n"
            elif "results" in category:
                results += group_text + "\n"
            elif "discussion" in category:
                discussion += group_text + "\n"
            elif "conclusion" in category:
                conclusion += group_text + "\n"
            elif "references" in category:
                references += group_text + "\n"
            
        self.categories["introduction"] = introduction 
        self.categories["methods"] = methods 
        self.categories["results"] = results
        self.categories["discussion"] = discussion 
        self.categories["conclusion"] = conclusion
        self.categories["references"] = references 
    
    def group_lines(self):
        return {
            'summary': "\n\n\n".join([self.categories["abstract"], self.categories["introduction"], self.categories["conclusion"]]),
            'background_significance': self.categories["introduction"] + '\n\n\n',
            'methods': self.categories["methods"] + '\n\n\n', 
            'results': self.categories["results"],
            'discussion': self.categories["discussion"],
            'references': self.categories["references"],
        }
    
    def summarize_sections(self, organized_sections): 
        title_prompt = f"Context:{self.categories['title']}" + self.get_title_prompt() 
        author_prompt = f"Context{self.categories['authors']}" + self.get_author_prompt()
        summary_prompt = f"Context:{organized_sections.get('summary')}" + self.get_summary_prompt()
        background_significance_prompt = f"Context:{organized_sections.get('background_significance')}" + self.get_background_significance_prompt()
        methods_prompt = f"Context:{organized_sections.get('methods')}" + self.get_methods_prompt()
        results_prompt = f"Context:{organized_sections.get('results')}" + self.get_results_prompt()
        discussion_prompt = f"Context:{organized_sections.get('discussion')}" + self.get_discussion_prompt()
        references_prompt = f"Context:{organized_sections.get('references')}" + self.get_references_prompt()

        """category = ollama.generate(model = "llama3", prompt = prompt_template)
            print(f"Groq classification for group {idx + 1}: {category['response'].strip().lower()}")
        """
        
        title_response = ollama.generate(model = "llama3", prompt = title_prompt)
        author_response = ollama.generate(model = "llama3", prompt = author_prompt)
        summary_response = ollama.generate(model = "llama3", prompt = summary_prompt)
        background_significance_response = ollama.generate(model = "llama3", prompt = background_significance_prompt)
        methods_response = ollama.generate(model = "llama3", prompt = methods_prompt)
        results_response = ollama.generate(model = "llama3", prompt = results_prompt)
        discussion_response = ollama.generate(model = "llama3", prompt = discussion_prompt)
        references_response = ollama.generate(model = "llama3", prompt = references_prompt)
        
        paper_summary = (title_response['response'] + '\n\n\n' + 
                            author_response['response'] + '\n\n\n' + 
                            summary_response['response'] + '\n\n\n' + 
                            background_significance_response['response'] + '\n\n\n' + 
                            methods_response['response'] + '\n\n\n' + 
                            results_response['response'] + '\n\n\n' + 
                            discussion_response['response'] + '\n\n\n' + 
                            references_response['response'])
        
        return paper_summary

    def get_title_prompt(self):
        return "Set the title for the section as '#Title' Directly state the title of the paper. Disregard all other text."
    def get_author_prompt(self):
        return "Set the title for the section as '#Authors' State the names of the authors with their affiliations ONLY. Disregard all other information."
    def get_summary_prompt(self):
        return """Set the title for the section as '#Summary'. 
                
                __
                You are a summarizing AI tasked with summarizing key sections of a research paper. Please summarize the abstract, introduction, and conclusion into a single concise paragraph. 
                Focus on capturing the main objectives, methods, key findings, and conclusions from the abstract; the background, research question, and significance from the introduction;
                and the key results, implications, and future directions from the conclusion. 
                Ensure the summary is clear, specific, and informative without including unnecessary details.
                __
                
                Do not output anything you do not know for certain."""
    def get_background_significance_prompt(self):
        return """Set the title for the section as '#Background and Significance'
                
                __
                You are a summarizing AI. Please summarize the provided introduction focusing on the background and significance of the study. 
                Highlight the context, the research problem, key literature, and the importance of the study. Ensure the summary captures the rationale behind the research
                and its potential impact or contribution to the field, presented as a clean and concise background and significance section.
                __
                
                Do not output anything you do not know for certain."""
    def get_methods_prompt(self):
        return """Set the title for the section as '#Methods'
                
                __
                You are a summarizing AI. Please summarize the methods section (the provided section), focusing on the experimental design, procedures, materials, and techniques used in the study. 
                Ensure the summary captures the key steps, methodologies, and any relevant parameters or controls, presented as a clear and concise methods section.
                Output everything in a bulletpoint format.
                __
                
                Do not output anything you do not know for certain."""
    def get_results_prompt(self):
        return """"Set the title for the section as '#Results'
                
                __
                You are a summarizing AI. Please summarize the above results section from a research paper. Focus on the key findings, data trends, and any significant outcomes.
                Ensure that the summary is concise and accurately reflects the main results and their implications.
                Output the key results in a bulletpoint format.
                __
                
                Do not output anything you do not know for certain."""
    def get_discussion_prompt(self):
        return """Set the title for the section as '#Discussion'
                __
                You are a summarizing AI. Please summarize the above discussion section of a research paper. Highlight the key interpretations, implications, and 
                any connections made to the broader research context. Ensure the summary is concise and captures the essence of the authors' conclusions.
                __
                
                Do not output anything you do not know for certain.
                """
    def get_references_prompt(self):
        return """Set the title for the section as '#References'
                    
                __
                Iterate through every reference provided. 
                Only include the name of each paper. 
                __
                
                Do not output anything you do not know for certain."""
