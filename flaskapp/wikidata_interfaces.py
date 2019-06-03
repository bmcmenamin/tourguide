"""
    Classes for interfacing with WikiData
"""

import abc

import funcy
import requests


API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

class BaseRequester(abc.ABC):
    """Base class for findling links to/from a page"""

    INIT_PARAMS = None
    _PROP_TYPE = None #"links"
    _CONTINUE_FIELD = None # "plcontinue"
    _BATCH_SIZE = 1

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
            (
                pageid_data['title'].replace(" ", "_"),
                l['title'].replace(" ", "_")
            )
            for pageid_data in pages.values()
            for l in pageid_data.get(self._PROP_TYPE, [])
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str

    def _get_all_responses(self, params):
        resp = self.session.get(url=API_ENDPOINT, params=params)
        link_list, continue_str = self._parse_response(resp)

        while continue_str:

            params[self._CONTINUE_FIELD] = continue_str
            resp = self.session.get(
                url=API_ENDPOINT,
                params=params
            )
            _links, continue_str = self._parse_response(resp)
            link_list += _links

        return link_list

    def get_payload(self, page_titles):
        params = self.INIT_PARAMS.copy()

        results = []
        for chunk in funcy.chunks(self._BATCH_SIZE, page_titles):
            chunk = [str(c).replace(" ", "_") for c in chunk]
            params["titles"] = '|'.join(chunk)
            params.pop(self._CONTINUE_FIELD, None)
            resp = self._get_all_responses(params)
            results.extend(resp)

        return results

class OutLinkFinder(BaseRequester):

    _PROP_TYPE = "links"
    _CONTINUE_FIELD = "plcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "links",
        "redirects": 1,
        "plnamespace": 0,
        "pllimit": "max",
        "continue": "||"
    }

class InLinkFinder(BaseRequester):

    _PROP_TYPE = "linkshere"
    _CONTINUE_FIELD = "lhcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "linkshere",
        "redirects": 1,
        "lhprop": "title",
        "lhnamespace": 0,
        "lhlimit": "max",
    }

class NearbyFinder(BaseRequester):

    _PROP_TYPE = "geosearch"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "list": "geosearch",
        "gsradius":10000,
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
            place['title'].replace(" ", "_")
            for place in places
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str

    def get_payload(self, lat, lon, num_nearby=10):
        params = self.INIT_PARAMS.copy()
        params["gscoord"] = "{}|{}".format(lat, lon)
        params["gslimit"] = num_nearby
        return self._get_all_responses(params)

class CategoryFinder(BaseRequester):

    _PROP_TYPE = "categories"
    _CONTINUE_FIELD = "clcontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "categories",
        "cllimit": "max",
        "clshow": "!hidden"
    }

class CoordinateFinder(BaseRequester):

    _PROP_TYPE = "coordinates"
    _CONTINUE_FIELD = "cocontinue"
    INIT_PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "coordinates",
        "colimit": "max"
    }

    def _parse_response(self, resp):

        resp_dict = resp.json()

        pages = (
            resp_dict.
            get("query", {}).
            get("pages", {})
        )

        links = [
            (
                pageid_data['title'].replace(" ", "_"),
                l.get('dist', -1)
            )
            for pageid_data in pages.values()
            for l in pageid_data.get(self._PROP_TYPE, [])
        ]

        continue_str = (
            resp_dict.
            get('continue', {}).
            get(self._CONTINUE_FIELD)
        )

        return links, continue_str

    def get_payload(self, page_titles, latlon):
        params = self.INIT_PARAMS.copy()
        params["codistancefrompoint"] = "{}|{}".format(*latlon)
        for chunk in funcy.chunks(50, page_titles):
            chunk = [str(c).replace(" ", "_") for c in chunk]
            params.pop(self._CONTINUE_FIELD, None)
            params["titles"] = '|'.join(chunk)
            return self._get_all_responses(params)

