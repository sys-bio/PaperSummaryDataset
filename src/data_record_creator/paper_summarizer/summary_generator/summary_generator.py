from src.utils import llm_caller_base
import os
import tempfile
import fitz
import pymupdf4llm
import pathlib

class SummaryGenerator(llm_caller_base.LLMCallerBase):
    def __init__(self):
        super().__init__()
        self._paper_sections = {}
        self._category_sections = {}
        self._categories = {'abstract', 'discussion', 'references', 'conclusion', 'introduction','results', 'methodologies', 'methods', 'methodology', 'background'}

    def generate(self, paper_file, feedback=""):
        self._paper_sections = self._extract_paper_sections(self, paper_file)
        return "# Paper summary \n\n" + self._get_paper_summary(feedback)

    def get_paper_sections(self):
        return self._paper_sections

    @staticmethod
    def _extract_paper_sections(self, paper_file):
        LOCAL_DOWNLOAD_DIR = tempfile.mkdtemp()
        os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
        pdf_document = fitz.open(paper_file)
        outname_md = os.path.join(LOCAL_DOWNLOAD_DIR, f"pre_file.md")
        md_text = pymupdf4llm.to_markdown(pdf_document) 
        pathlib.Path(outname_md).write_bytes(md_text.encode())

        with open(outname_md, 'r', encoding='utf-8') as file:
            content = file.read()

        sections = []
        current_section = []

        for line in content.splitlines():
            if line.startswith(('**', '##', '#')):
                if current_section:
                    sections.append('\n'.join(current_section))
                    current_section = []
                current_section.append(line)
            else:
                if current_section or line.strip():
                    current_section.append(line)
                    
        with open(outname_md, 'r', encoding='utf-8') as file:
                lines_list = file.readlines()

        for section in sections:
            lines = section.splitlines()
            title2 = lines[:6]
            title = '\n'.join(title2)
            for category in self._categories:
                if category in title.lower():
                    self._category_sections[category] = section


        methods2 = []
        results2 = []
        in_methods = False
        in_results = False

        #some variables are not defined below 
        
        for line in lines_list:
            if 'Methods' in line:
                in_methods = True
                continue  # Skip the line containing 'Methods'
            if 'Results' in line:
                in_results = True
                in_methods = False
                continue  # Skip the line containing 'Results'
            if 'Discussion' in line or 'Conclusion' in line or 'References' in line:
                in_results = False
                break  # Stop if we've reached the Discussion or Conclusion

            if in_methods:
                methods2.append(line)
            elif in_results:
                results2.append(line)

        methods_text = ''.join(methods2).strip()
        results_text = ''.join(results2).strip()

        if len(methods_text.strip()) == 0:
            methods_text = self._category_sections.get('methods')
            if len(methods_text.strip()) == 0:
                methods_text = self._category_sections.get('methodologies')
                if len (methods_text.strip()) == 0:
                    methods_text = self._category_sections.get('methodology') or ''
                    
        if len(results_text.strip()) == 0:
            results_text = self._category_sections.get('results') or ''
            
        if len(methods_text.strip()) == 0 and len(results_text.strip()) == 0:
            intro_index = next((i for i, sec in enumerate(sections) if 'introduction' in sec.lower()), None)
            results_index = next((i for i, sec in enumerate(sections) if 'results' in sec.lower()), None)
            discussion_index = next((i for i, sec in enumerate(sections) if 'discussion' in sec.lower()), None)

            if intro_index is not None:
                if results_index is not None:
                    methods_text = "\n".join(sections[intro_index + 1:results_index])
                    results_text = sections[results_index]
                elif discussion_index is not None:
                    methods_text = "\n".join(sections[intro_index + 1:discussion_index])
                    results_text = "\n".join(sections[results_index:discussion_index])
                else:
                    methods_text = "\n".join(sections[intro_index + 1:])

        if len(results_text.strip()) == 0:
            results_text = self._category_sections.get('results') or ''
    
        abstract = '\n'.join(sections[:15])
        introduction = self._category_sections.get('introduction') or ''
        conclusion = self._category_sections.get('conclusion') or ''
        discussion2 = self._category_sections.get('discussion') or ''
        references = self._category_sections.get('references') or ''

        if len(discussion2.strip()) == 0:
            discussion2 = conclusion
        
        if len(introduction.strip()) == 0:
            introduction = self._category_sections.get('background') or ''
        if isinstance(sections, str):
            sections = sections.split('\n\n\n')

        # Extract title and author
        title1 = '\n'.join(sections[:5])
        author = '\n'.join(sections[0:4])
        
        summary = "\n\n\n".join([abstract, introduction, conclusion])
        background_significance = introduction + '\n\n\n'
        
        title1 = '\n'.join(title1) if isinstance(title1, list) else title1
        author = '\n'.join(author) if isinstance(author, list) else author
        summary = '\n'.join(summary) if isinstance(summary, list) else summary
        background_significance = '\n'.join(background_significance) if isinstance(background_significance, list) else background_significance
        methods = '\n'.join(methods_text) if isinstance(methods_text, list) else methods_text
        results = '\n'.join(results_text) if isinstance(results_text, list) else results_text
        discussion = '\n'.join(discussion2) if isinstance(discussion2, list) else discussion2
        references = '\n'.join(references) if isinstance(references, list) else references
        
        paper_sections = {'title': title1, 'authors': author, 'summary': summary,
                      'background_significance': background_significance, 'methods': methods,
                      'results': results, 'discussion': discussion, 'references': references}

        return paper_sections
                    
    def _get_paper_summary(self, feedback=""):
        paper_summary = "## This is the summary of " + self._paper_sections['title'] + " paper \n\n"
        title_prompt = f"Context: {self._paper_sections['title']}" + self.get_title_prompt()
        author_prompt = f"Context: {self._paper_sections['authors']}" + self.get_author_prompt()
        summary_prompt = f"Context:{self._paper_sections['summary']}" + self.get_summary_prompt()
        background_significance_prompt = f"Context:{self._paper_sections['background_significance']}" + self.get_background_significance_prompt()
        methods_prompt = f"Context:{self._paper_sections['methods']}" + self.get_methods_prompt()
        results_prompt = f"Context:{self._paper_sections['results']}" + self.get_results_prompt()
        discussion_prompt = f"Context:{self._paper_sections['discussion']}" + self.get_discussion_prompt()
        references_prompt = f"Context:{self._paper_sections['references']}" + self.get_references_prompt()

        title_response = self.response_generator.generate(title_prompt)
        author_response = self.response_generator.generate(author_prompt)
        summary_response = self.response_generator.generate(summary_prompt)
        background_significance_response = self.response_generator.generate(background_significance_prompt)
        methods_response = self.response_generator.generate(methods_prompt)
        results_response = self.response_generator.generate(results_prompt)
        discussion_response = self.response_generator.generate(discussion_prompt)
        references_response = self.response_generator.generate(references_prompt)

        paper_summary = "## This is the summary of " + self._paper_sections['title'] + " paper \n\n" + "\n\n\n" + title_response + "\n\n\n" + author_response + "\n\n\n" + summary_response + "\n\n\n" + background_significance_response + "\n\n\n" + methods_response + "\n\n\n" + results_response + "\n\n\n" + discussion_response + "\n\n\n" + references_response 
        #  Make use of the last round feedback if available
        # In this class you can make a call like this:
        # response = self.response_generator.generate(prompt) to pass a prompt to the llm model and get the response
        return paper_summary #want to assign it to a file or just return it?
    
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
