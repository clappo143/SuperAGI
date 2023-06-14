from typing import Type, Optional, Any
from pydantic import BaseModel, Field
import aiohttp
from superagi.helper.google_serp import GoogleSerpApiWrap
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool
from superagi.config.config import get_config

import os

import json


class GoogleSerpSchema(BaseModel):
    query: str = Field(
        ...,
        description="The search query for Google SERP.",
    )
    search_type: str = Field(
        "search",
        description="The type of search to perform. Can be 'search' or 'news'.",
    )

class GoogleSerpTool(BaseTool):
    llm: Optional[BaseLlm] = None
    name = "GoogleSerp"
    description = (
        "A tool for performing a Google SERP search or news search and extracting snippets and webpages."
        "Input should be a search query and the type of search ('search' or 'news')."
    )
    args_schema: Type[GoogleSerpSchema] = GoogleSerpSchema

    class Config:
        arbitrary_types_allowed = True

    def _execute(self, query: str, search_type: str = "search") -> tuple:
        api_key = get_config("SERP_API_KEY")
        serp_api = GoogleSerpApiWrap(api_key)
        response = serp_api.search_run(query, search_type)
        summary, links = self.summarise_result(query, response["snippets"], response["links"])
        if len(links) > 0:
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])
        return summary

    def summarise_result(self, query, snippets, links):
        summarize_prompt = """Review the following text `{snippets}` and links:
        {links}
        - Provide a structured list of the results, including Titles, Author or Publication, Date and URL. 
        - Write a summary and attempt to answer the query: `{query}` based on the snippets and links.
        EXAMPLE RESPONSE: 
        - Title: How to Bake Chocolate Chip Cookies  
        - Author: Betty Crocker
        - Date: 24 March 2019
        - Publication: AllRecipes
        - URL: https://www.allrecipes.com/recipe/9956/best-chocolate-chip-cookies/
        In summary, based on the Google search results, snippets and links, to bake chocolate chip cookies...  """

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{query}", query)
        summarize_prompt = summarize_prompt.replace("{links}", str(links))

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)
        return result["content"], links