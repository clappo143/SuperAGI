import urllib.parse
import json
from typing import Type, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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
    fields_to_extract: Optional[list[str]] = Field(
        None,
        description="Optional list of fields to extract from the webpage. Can include 'title', 'text', 'author', etc.",
    )


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
        "Used to scrape website URLs and extract text content. Can handle **valid** URLs for specific site searches but can generate Google (with date range parameter) and Bing search queries as fallback if invalid URL is initially supplied."
    )
    args_schema: Type[WebScraperSchema] = WebScraperSchema

    class Config:
        arbitrary_types_allowed = True

    def generate_search_url(self, base_url, query, site=None, start_date=None, end_date=None):
        query = urllib.parse.quote_plus(query)  # URL encode the query

        # Add site search parameter
        if site:
            query += f"+site:{urllib.parse.quote_plus(site)}"

        # Add date parameters
        if start_date and end_date:
            query += f"&tbs=cdr:1,cd_min:{start_date},cd_max:{end_date}"

        return base_url + query

    def generate_google_search_url(self, query, site=None, start_date=None, end_date=None):
        base_url = "https://www.google.com/search?q="
        return self.generate_search_url(base_url, query, site, start_date, end_date)

    def generate_bing_search_url(self, query, site=None):
        base_url = "https://www.bing.com/search?q="
        return self.generate_search_url(base_url, query, site)

    def extract_field_from_html(self, field, soup):
        if field == "title":
            return soup.title.text if soup.title else None

        if field == "text":
            paragraphs = [p.text for p in soup.find_all('p')]
            return ' '.join(paragraphs)

        if field == "author":
            author_div = soup.find("div", class_="author")
            return author_div.text if author_div else None

        if field == "article_info":
            headline = soup.find("h1").text if soup.find("h1") else None
            publisher = soup.find("div", class_="publisher").text if soup.find("div", class_="publisher") else None
            publication_date = soup.find("time")["datetime"] if soup.find("time") else None
            summary = soup.find("div", class_="summary").text[:300] if soup.find("div", class_="summary") else None

            return {
                "Headline": headline,
                "Publisher": publisher, 
                "Date": publication_date,
                "Summary": summary
            }

        # Add more fields as needed....

        return None

    def _execute(self, website_url: str, site: str = None, start_date: str = None, end_date: str = None, fields_to_extract: list[str] = None) -> str:
        """
        Execute the Web Scraper tool.

        Args:
        website_url : The website url to scrape or a search query.
        fields_to_extract : A list of fields to extract from the webpage.

        Returns:
        A JSON string containing the extracted data.
        """
        # Check if the website_url is a valid URL
        try:
            response = requests.head(website_url)
            response.raise_for_status()
        except (requests.RequestException, ValueError):
            # If not, treat it as a search query
            if "google" in website_url:
                website_url = self.generate_google_search_url(website_url, site, start_date, end_date)
            elif "bing" in website_url:
                website_url = self.generate_bing_search_url(website_url, site)

        try:
            content = WebpageExtractor().extract_with_bs4(website_url)
        except Exception as e:
            return json.dumps({"error": f"Failed to extract content from {website_url}: {e}"})

        soup = BeautifulSoup(content, "html.parser")
        data = {field: self.extract_field_from_html(field, soup) for field in fields_to_extract}

        return json.dumps(data, indent=4)
