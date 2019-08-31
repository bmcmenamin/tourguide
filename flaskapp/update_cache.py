"""
    Run scripts on most-viewed pages to keep the cache relevant
"""

import requests
import wikidata_interfaces as wi

BATCH_SIZE = 100
MAX_PAGES = 10000


def yield_page_titles(max_pages, batch_size=BATCH_SIZE):

    params = {
        "action": "query",
        "format": "json",
        "list": "mostviewed",
        "pvimlimit": str(batch_size)
    }

    for offset in range(0, max_pages, batch_size):
        params["pvimoffset"] = str(offset)

        pages = (
            requests
            .Session()
            .get(
                url=wi.API_ENDPOINT,
                params=params
            )
            .json()
            .get("query", {})
            .get("mostviewed", {})
        )

        yield [p['title'] for p in pages]


def main(max_pages):

    cacher_funcs = [
        wi.OutLinkFinder().get_payload,
        wi.InLinkFinder().get_payload,
        wi.CategoryFinder().get_payload,
    ]

    for page_titles in yield_page_titles(max_pages):
        for func in cacher_funcs:
            func(page_titles)


if __name__ == "__main__":
    main(MAX_PAGES)
