from datetime import datetime
from typing import Type, Optional
from urllib.parse import urlparse, quote_plus

from pydantic import BaseModel, Field, validator

from superagi.helper.webpage_extractor import WebpageExtractor
from superagi.llms.base_llm import BaseLlm
from superagi.tools.base_tool import BaseTool


class WebScraperSchema(BaseModel):
    website_url: str = Field(
        ...,
        description="Valid website URL without any quotes. Can include search parameters for specific sites and date ranges.",
    )
    site: Optional[str] = Field(
        None,
        description="Optional specific site to search within.",
    )
    start_date: Optional[str] = Field(
        None,
        description="Optional start date for date range search. Format: MM/DD/YYYY",
    )
    end_date: Optional[str] = Field(
        None,
        description="Optional end date for date range search. Format: MM/DD/YYYY",
    )

    @validator("start_date", "end_date", pre=True, always=True)
    def convert_date_format(cls, value):
        if value:
            return datetime.strptime(value, "%m/%d/%Y").strftime("%m-%d-%Y")
        return value


class WebScraperTool(BaseTool):
    """
    Web Scraper tool

    Attributes:
        name : The name.
        description : The description.
        args_schema : The args schema.
    """
    llm: Optional[BaseLlm] = None
    name = "WebScraperTool"
    description = (
        "Used to scrape website URLs and extract text content. Can handle URLs for specific site searches and date range searches."
    )
    args_schema: Type[WebScraperSchema] = WebScraperSchema

    class Config:
        arbitrary_types_allowed = True

    def generate_search_url(self, query, site=None, start_date=None, end_date=None):
        base_url = "https://www.google.com/search?q="
        query = quote_plus(query)  # URL encode the query

        # Add site search parameter
        if site:
            query += f"+site:{quote_plus(site)}"

        # Add date parameters
        if start_date and end_date:
            query += f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"

        return base_url + query

    def _execute(self, website_url: str, site: str = None, start_date: str = None, end_date: str = None) -> tuple:
        """
        Execute the Web Scraper tool.

        Args:
            website_url : The website url to scrape.

        Returns:
            The text content of the website.
        """
        # Check if the website_url is a valid URL
        result = urlparse(website_url)
        if not all([result.scheme, result.netloc]):
            # If not, try to generate a search URL
            website_url = self.generate_search_url(website_url, site, start_date, end_date)

        content = WebpageExtractor().extract_with_bs4(website_url)
        max_length = len(' '.join(content.split(" ")[:600]))
        return content[:max_length]
