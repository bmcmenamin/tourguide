"""
    Classes for interfacing with WikiData
"""

import abc
import logging

import requests


API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

logging.basicConfig(level=logging.INFO)


class BaseRequester(abc.ABC):
    """Base class for finding links to/from a page"""

    INIT_PARAMS = None
    _PROP_TYPE = None
    _CONTINUE_FIELD = None
    _BATCH_SIZE = 5

    def __init__(self):
        self.session = requests.Session()

    def _parse_response(self, resp):
        resp_dict = resp.json()
        pages = resp_dict.get("query", {}).get("pages", {})
        links = [
            {
                "x0": pageid_data['title'].replace(" ", "_"),
                "x1": el['title'].replace(" ", "_")
            }
            for pageid_data in pages.values()
            for el in pageid_data.get(self._PROP_TYPE, [])
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str

    def _get_api_responses(self, params):

        resp = self.session.get(url=API_ENDPOINT, params=params)
        link_list, continue_str = self._parse_response(resp)

        while continue_str:
            logging.info("Continuing queries on %s", type(self).__name__)
            params[self._CONTINUE_FIELD] = continue_str
            resp = self.session.get(url=API_ENDPOINT, params=params)
            _links, continue_str = self._parse_response(resp)
            link_list += _links

        return link_list

    def get_payload(self, page_titles):

        params = self.INIT_PARAMS.copy()

        page_titles = (
            str(p).replace(" ", "_")
            for p in page_titles
        )

        results = []
        for page_title in page_titles:

            params["titles"] = page_title
            params.pop(self._CONTINUE_FIELD, None)
            result = self._get_api_responses(params)
            results.extend(result)

        return results


class FulltextFinder(BaseRequester):
    _PROP_TYPE = "revisions"
    _CONTINUE_FIELD = "rvcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "rvprop": "content",
        "redirects": 1,
        "continue": "||"
    }


class PageidFinder(BaseRequester):
    _PROP_TYPE = "info"
    _CONTINUE_FIELD = "incontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "redirects": 1,
        "continue": "||"
    }

    def _parse_response(self, resp):
        resp_dict = resp.json()
        pages = resp_dict.get("query", {}).get("pages", {})
        links = [
            (pageid_data['title'], int(pageid))
            for pageid, pageid_data in pages.items()
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str