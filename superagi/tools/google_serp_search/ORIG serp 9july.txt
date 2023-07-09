from typing import Type, Optional, Any
from pydantic import BaseModel, Field
import aiohttp
from superagi.helper.google_serp import GoogleSerpApiWrap
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool
import os

import json5 as json 


class GoogleSerpSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search (_execute) or news (news_execute) query for Google SERP.",
    )


'''Google search (_execute) and news (news_execute) using serper.dev. Use server.dev api keys'''
class GoogleSerpTool(BaseTool):
    """
    Google Search tool

    Attributes:
        name : The name.
        description : The description.
        args_schema : The args schema.
    """
    llm: Optional[BaseLlm] = None
    name = "GoogleSerp"
    description = (
        "A tool for performing a Google SERP search and extracting snippets and webpages."
        "It can also fetch news results related to a given query."
        "Input should be a search query."
    )

    args_schema: Type[GoogleSerpSchema] = GoogleSerpSchema

    class Config:
        arbitrary_types_allowed = True

    def _execute(self, query: str) -> tuple:
        """
        Execute the Google search tool.

        Args:
            query : The query to search for.

        Returns:
            Search result summary along with related links
        """
        api_key = self.get_tool_config("SERP_API_KEY")
        serp_api = GoogleSerpApiWrap(api_key)
        response = serp_api.search_run(query)
        summary, links = self.summarise_result(query, response["snippets"], response["links"])
        if len(links) > 0: 
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])   
        return summary

    def news_execute(self, query: str) -> tuple:
        api_key = self.get_tool_config("SERP_API_KEY")
        serp_api = GoogleSerpApiWrap(api_key)
        response = serp_api.news_run(query)
        summary, links = self.summarise_result(query, response["snippets"], response["links"])
        if len(links) > 0:
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3]) 
        return summary

    def summarise_result(self, query, snippets, links):
        summarize_prompt = """Review the following text `{snippets}`and links:
        {links}
        - A) Provide a summarised list of the results, including Titles, Author or Publication, Date and URL. 
        - B) Write a concise or as descriptive as necessary summary and attempt to
            answer the query: `{query}` as best as possible based on the snippets and links.
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
        
        In summary, based on the Google search results, snippets and links, to bake chocolate chip cookies...  """

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{query}", query)
        summarize_prompt = summarize_prompt.replace("{links}", str(links))

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)
        return result["content"], links 