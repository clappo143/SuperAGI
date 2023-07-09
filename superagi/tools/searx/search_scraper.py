import random
from typing import List, Dict
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from superagi.lib.logger import logger
import time
from fake_useragent import UserAgent
import json

searx_hosts = [
    "https://searx.catfluori.de/",
    "https://search.mdosch.de/",
    "https://darmarit.org/searx/",
    "https://xo.wtf/",
    "https://search.rowie.at/",
    "https://searx.namejeff.xyz/",
    "https://search.demoniak.ch/",
    # Add more instances here e.g. https://search.im-in.space/; https://search.kiwitalk.de/ ;  https://searx.mha.fi/ (See: https://searx.space/)
    # (GPT-4 25 June) # These instances have high TLS and CSP ratings, support HTML responses, use well-known certificate authorities, have high uptime percentages, and relatively low response times.
]

class SearchResult(BaseModel):
    id: int
    title: str
    link: str
    description: str
    sources: List[str]

    def __str__(self):
        return f"{self.id}. {self.title} - {self.link}\n{self.description}"

def search_results(query: str, language: str) -> str:
    ua = UserAgent()
    random.shuffle(searx_hosts)
    for searx_url in searx_hosts:
        res = httpx.get(
            searx_url + "/search",
            params={"q": query, "language": language},
            headers={"User-Agent": ua.random},
        )
        time.sleep(2)
        if res.status_code == 200:
            results = scrape_results(res.text)
            if results:
                snippets = [str(result) for result in results]
                links = [result['link'] for result in results]
                output_dict = {"snippets": snippets, "links": links}
                return json.dumps(output_dict)
            else:
                empty_output_dict = {"snippets": [], "links": []}
                return json.dumps(empty_output_dict)
        else:
            logger.info(res.status_code, searx_url)

    raise Exception("All Searx instances returned non-200 status codes")

def clean_whitespace(s: str):
    return " ".join(s.split())

def scrape_results(html: str) -> List[SearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    result_divs = soup.find_all(attrs={"class": "result"})
    
    result_list = []
    n = 1
    for result_div in result_divs:
        if result_div is None:
            continue
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
