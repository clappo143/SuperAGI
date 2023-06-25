import random
import requests
from typing import List
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
import time

# The delay between requests in seconds
delay = 1

def get_searx_instances():
    response = requests.get('https://searx.space/data/instances.json')
    data = response.json()

    # Filter out instances that are currently offline, have an HTTPS grade of 'A+' and an Observatory grade of 'A+'
    secure_instances = [url for url, info in data.items() if info['status'] == 'ok' and info['https_grade'] == 'A+' and info['observatory_grade'] == 'A+']

    return secure_instances

searx_hosts = get_searx_instances()

class SearchResult(BaseModel):
    """
    Represents a single search result from Searx

    Attributes:
        id : The ID of the search result.
        title : The title of the search result.
        link : The link of the search result.
        description : The description of the search result.
        sources : The sources of the search result.
    """
    id: int
    title: str
    link: str
    description: str
    sources: List[str]

    def __str__(self):
        return f"""{self.id}. {self.title} - {self.link} 
{self.description}"""

def search(query):
    """
    Gets the raw HTML of a searx search result page

    Args:
        query : The query to search for.
    """
    searx_url = random.choice(searx_hosts)
    res = httpx.get(
        searx_url + "/search", params={"q": query}, headers={"User-Agent": "Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/114.0"}
    )
    if res.status_code != 200:
        raise Exception(f"Searx returned {res.status_code} status code")

    # Wait for the specified delay before sending the next request
    time.sleep(delay)

    return res.text

def clean_whitespace(s: str):
    """
    Cleans up whitespace in a string

    Args:
        s : The string to clean up.

    Returns:
        The cleaned up string.
    """
    return " ".join(s.split())

def scrape_results(html):
    """
    Converts raw HTML into a list of SearchResult objects

    Args:
        html : The raw HTML to convert.

    Returns:
        A list of SearchResult objects.
    """
    soup = BeautifulSoup(html, "html.parser")
    result_divs = soup.find_all(attrs={"class": "result"})
    
    result_list = []
    n = 1
    for result_div in result_divs:
        if result_div is None:
            continue
        # Needed to work on multiple versions of Searx
        header = result_div.find(["h4", "h3"])
        if header is None:
            continue
        link_element = header.find("a")
        if link_element is None:
            continue
        link = link_element["href"]
        title = header.text.strip()

        description_element = result_div.find("p")
        if description_element is None:
            continue
        description = clean_whitespace(description_element.text)

        # Needed to work on multiple versions of Searx
        sources_container = result_div.find(
            attrs={"class": "pull-right"}
        ) or result_div.find(attrs={"class": "engines"}) 
        source_spans = sources_container.find_all("span")
        sources = []
        for s in source_spans:
            sources.append(s.text.strip())

        result = {
            'id': n,
            'title': title,
            'link': link,
            'description': description,
            'sources': sources
        }
        result_list.append(result)
        n += 1

    return result_list


def search_results(query):
    '''Returns a dictionary with "snippets" and "links" as keys'''
    results = scrape_results(search(query))
    return {
        "snippets": [str(result) for result in results],
        "links": [result['link'] for result in results]
    }
