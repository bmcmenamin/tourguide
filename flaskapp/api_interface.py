"""
    Classes for interfacing with WikiData
"""
import abc
import functools
import requests

class BaseLinkFinder(abc.ABC):
    """Base class for findling links to/from a page"""

    API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
    INIT_PARAMS = None
    _PROP_TYPE = None #"links"
    _CONTINUE_FIELD = None # "plcontinue"

    def __init__(self):
        self.session = requests.Session()

    def _parse_response(self, resp):

        resp_dict = resp.json()

        pages = (
            resp_dict.
            get("query", {}).
            get("pages", {})
        )

        links = [
            l['title']
            for pageid_data in pages.values()
            for l in pageid_data.get(self._PROP_TYPE, [])
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str

    def _get_all_responses(self, params, cutoff=None):
        resp = self.session.get(url=self.API_ENDPOINT, params=params)
        link_list, cont_str = self._parse_response(resp)
        while cont_str:

            if cutoff is not None and len(link_list) > cutoff:
                return []

            params[self._CONTINUE_FIELD] = cont_str
            resp = self.session.get(
                url=self.API_ENDPOINT,
                params=params
            )
            _links, cont_str = self._parse_response(resp)
            link_list += _links

        return link_list

    @functools.lru_cache(maxsize=10000)
    def get_links(self, page_title, cutoff=None):
        params = self.INIT_PARAMS.copy()
        params["titles"] = page_title
        return self._get_all_responses(params, cutoff=cutoff)


class OutLinkFinder(BaseLinkFinder):

    _PROP_TYPE = "links"
    _CONTINUE_FIELD = "plcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "links",
        "list": "meta",
        "plnamespace": 0,
        "pllimit": 500,
        "redirects": 1,
        "continue": "||"
    }


class InLinkFinder(BaseLinkFinder):

    _PROP_TYPE = "linkshere"
    _CONTINUE_FIELD = "lhcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "linkshere",
        "lhprop": "title",
        "list": "meta",
        "lhnamespace": 0,
        "redirects": 1,
        "lhlimit": "max",
        "lhcontinue": ""
    }


class NearbyFinder(BaseLinkFinder):

    _PROP_TYPE = "geosearch"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "prop": "title",
        "gsradius":10000,
        "gslimit": 50,
        "gsnamespace": 0,
        "gsprop": "name",
        "gsprimary": "primary"
    }

    def _parse_response(self, resp):

        resp_dict = resp.json()

        places = (
            resp_dict.
            get("query", {}).
            get(self._PROP_TYPE, [])
        )

        links = [
            place['title']
            for place in places
        ]

        continue_str = ""

        return links, continue_str

    @functools.lru_cache(maxsize=10000)
    def get_links(self, lat, lon):
        params = self.INIT_PARAMS.copy()
        params["gscoord"] = "{}|{}".format(lat, lon)
        return self._get_all_responses(params)
