from typing import Type, Optional
from pydantic import BaseModel, Field
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool
from superagi.tools.searx.search_scraper import search, search_results, scrape_results 


class SearxSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for the Searx search engine.",
    )
    language: str = Field(
        ...,
        description="The language for the Searx search engine as a two letter code e.g. hi",
    )

class SearxSearchTool(BaseTool):
    llm: Optional[BaseLlm] = None
    name = "SearxSearch"
    description = (
        "A tool for performing a Searx search and extracting snippets and webpages."
        "Input should be a search query. Language (en, de etc) to be provided in language field"
    )
    args_schema: Type[SearxSearchSchema] = SearxSearchSchema

    class Config:
        arbitrary_types_allowed = True

    
    def _execute(self, query: str) -> tuple:
        response = search_results(query)
        summary, links = self.summarise_result(query, response["snippets"], response["links"])
        if len(links) > 0: 
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])   
        return summary

    def summarise_result(self, query, snippets, links):
        summarize_prompt = """Review the following text `{snippets}` and:
         - A) Provide a summarised list of the results: Include Titles, Author/Publication, Date and URL. 
        
        - B) Provide a concise summary of the collective results and their relevance to the task. Evaluate the performance of the`{query}` and consider possible imporovements.
        
        ---
        EXAMPLE RESPONSE: 
        [Summary of key snippets]
        
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
        The results were mainly related to baking and thus not very relevant to our use case about a criminal nicknamed 'cookie'. The current `{query}` is thus suboptimal and needs refinement. We should consider adding exclusionary operators/clauses (e.g. `cookie -baking -recipe`) for more focussed and relevant results. Alertnatively, we could try using a different TOOL.
        """

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{query}", query)
        summarize_prompt = summarize_prompt.replace("{links}", str(links))

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)
        return result["content"]
