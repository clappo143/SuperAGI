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
        description="Google general search using serper API",
    )

    news_query: str = Field(
        ...,
        description="Google news search using serper API",
    )

class GoogleSerpTool(BaseTool):
    llm: Optional[BaseLlm] = None
    name = "GoogleSerp"
    description = "Perform a general Google search using the GoogleSerp API. Input should be a search query."
    news_description = "Perform a Google news search using the GoogleSerp API. Input should be a search query."
    args_schema: Type[GoogleSerpSchema] = GoogleSerpSchema
    class Config:
        arbitrary_types_allowed = True

    def general_search(self, query: str) -> tuple:
        api_key = self.get_tool_config("SERP_API_KEY")
        serp_api = GoogleSerpApiWrap(api_key)
        response = serp_api.run(query)

        # Call summarise_result with the appropriate arguments
        summary, links = self.summarise_result(query, response["snippets"], response["links"], search_type='general')

        if len(links) > 0:
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])
        return summary

    def news_search(self, news_query: str) -> tuple:
        api_key = self.get_tool_config("SERP_API_KEY")
        serp_api = GoogleSerpApiWrap(api_key)
        response = serp_api.run(news_query, search_type='news')

        # Call summarise_result with the appropriate arguments
        summary, links = self.summarise_result(news_query, response["snippets"], response["links"], search_type='news')

        if len(links) > 0:
            return summary + "\n\nLinks:\n" + "\n".join("- " + link for link in links[:3])
        return summary

    def summarise_result(self, query, snippets, links, search_type='general'):
        # Modify the prompt to indicate the search type
        if search_type == 'general':
            search_type_text = "general search"
        else:
            search_type_text = "news search"

        summarize_prompt = """Review the following text `{snippets}`and links:
        {links}
        - A) Provide a summarised list of the results:
        `{snippets}`
        Include Titles, Author/Publication, Date and URL.

        - B) Provide a concise summary of the collective results and their relevance to the task. Evaluate the performance of the`{query}` and consider possible improvements.

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
        The results were mainly related to baking and thus not very relevant to our use case about a criminal nicknamed 'cookie'. The current `{query}` is thus suboptimal and needs refinement. We should consider adding exclusionary operators/clauses (e.g. `cookie -baking -recipe`) for more focussed and relevant results. Alternatively, we could try using a different TOOL.
        """

        summarize_prompt = summarize_prompt.replace("{snippets}", str(snippets))
        summarize_prompt = summarize_prompt.replace("{links}", "\n".join(links))

        messages = [{"role": "system", "content": summarize_prompt}]
        result = self.llm.chat_completion(messages, max_tokens=self.max_token_limit)

        # Prepare the result dictionary
        result_dict = {
            "summary": result["content"],
            "links": links[:3]
        }

        # Return the result dictionary as a JSON string
        return json.dumps(result_dict, indent=4)