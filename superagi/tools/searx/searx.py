from typing import Type, Optional
import re  # Import the 're' module for regular expressions
from pydantic import BaseModel, Field
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool
from superagi.tools.searx.search_scraper import search, search_results, scrape_results

LANGUAGE_DESC = "The language for the Searx search engine as a two letter code e.g. hi"

class SearxSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for the Searx search engine.",
    )
    language: str = Field(
        ...,
        description=LANGUAGE_DESC)

class SearxSearchTool(BaseTool):
    ...
    # Add caching
    cache = {}

    def extract_author(self, snippet):  # Add 'self' argument
        byline = None
        for line in snippet.split("\n"):
            if "by" in line.lower() or "written by" in line.lower():
                byline = line
                break
        if byline:
            return byline.replace("By ", "").replace("Written by ", "")
        return ""

    # Add the 'extract_date' method here
    def extract_date(self, snippet: str) -> Optional[str]:
        date_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
        match = re.search(date_pattern, snippet)
        if match:
            return match.group(0)
        return None

    def _execute(self, query: str, language: str) -> tuple:
        # Check cache first
        if query in self.cache:
            response = self.cache[query]
        else:
            try:
                response = search_results(query, language, limit=5)
                # Add to cache
                self.cache[query] = response
            except Exception as e:
                # Handle exception
                print(f"Error accessing Searx API: {e}")
                return "Error accessing Searx search engine. Please try again later."

        summarize_prompt = """Review the following text `{snippets}` and links:
                {links}
                - A) Provide a summarized list of the results: `{snippets}` 
                  Include Titles, Author/Publication, Date, and URL.

                - B) Provide a brief summary of the collective results and their relevance to the task. Evaluate the `{query}` and suggest possible improvements.

                ---
                EXAMPLE RESPONSE:
                A)
                - Title: How to Bake Chocolate Chip Cookies
                - Author: Betty Crocker
                - Date: 24 March 2019
                - Publication: AllRecipes
                - URL: https://www.allrecipes.com/recipe/9956/best-chocolate-chip-cookies/

                [Summary of link content]

                - Title: The Science of Baking the Perfect Cookie
                - Date: 3 May 2020
                - Publication: The New York Times
                - URL: https://www.nytimes.com/2020/05/03/dining/science-perfect-chocolate-chip-cookie.html

                [Summary of link content]

                B)
                The results were mainly related to baking and thus not very relevant to our use case about a criminal nicknamed 'cookie'. The current `{query}` is suboptimal and needs refinement. We should consider adding exclusionary operators/clauses (e.g. `cookie -baking -recipe`) for more focused and relevant results. Alternatively, we could try using a different TOOL.
                """

        summary, links = self.summarise_result(query, response["snippets"], response["links"][:3])
        if links:
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links)
        return summary

    def summarise_result(self, query, snippets, links):  # This is where 'snippets' and 'links' are defined
        results = []

        for snippet, link in zip(snippets, links):
            # Add more metadata
            result = {
                "title": snippet.split("\n")[0],
                "content": snippet,
                "link": link,
                "date": self.extract_date(snippet),  # Add logic to extract date
                "author": self.extract_author(snippet)  # Call 'extract_author' with 'self'
            }
            results.append(result)

        # Use extractive summarization to generate summary
        summary = " ".join(result["title"] for result in results[:3])

        return summary, links[:3]