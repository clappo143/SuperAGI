from typing import Type, Optional
from pydantic import BaseModel, Field
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool
from superagi.tools.searx.search_scraper import search_results


class SearxSearchSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for the Searx search engine.",
    )

class SearxSearchTool(BaseTool):
    """
    Searx Search tool

    Attributes:
        name : The name.
        description : The description.
        args_schema : The args schema.
    """
    llm: Optional[BaseLlm] = None
    name = "SearxSearch"
    description = (
        "A tool for performing a Searx search and extracting snippets and webpages."
        "Input should be a search query."
    )
    args_schema: Type[SearxSearchSchema] = SearxSearchSchema

    class Config:
        arbitrary_types_allowed = True

    
    def _execute(self, query: str) -> tuple:
        """
        Execute the Searx search tool.

        Args:
            query : The query to search for.

        Returns:
            Snippets and links from the Searx search.
        """
        response = search_results(query)
        summary, links = self.summarise_result(query, response["snippets"], response["links"])
        if len(links) > 0: 
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])   
        return summary

    def summarise_result(self, query, snippets, links):
        """
        Summarise the result of the Searx search.

        Args:
            query : The query to search for.
            snippets : The snippets from the Searx search.

        Returns:
            A summary of the result.
        """
        summarize_prompt = """Review the following text `{snippets}`and links:
        {links}
        - A) Provide a summarised list of the results:
        `{snippets}` 
        Include Titles, Author/Publication, Date and URL. 
        
        - B) If relevant to the task, attempt to answer the query: `{query}` as best as possible based on the snippets and links.
        
        EXAMPLE RESPONSE: 
        [Summary of key snippets]
        
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
        
        Write a concise or as descriptive as necessary and attempt to
            answer the query: `{query}` as best as possible. Use markdown formatting for
            longer responses."""

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{query}", query)
        summarize_prompt = summarize_prompt.replace("{links}", str(links))

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)
        return result["content"], links 
