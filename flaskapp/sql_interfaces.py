"""
    Classes to interact with CloudSQL wiki dumps
"""

import abc
import collections
import traceback
import os

import pymysql


DB_USERNAME_ENVVAR = "WIKIDB_USERNAME"
DB_PASSWORD_ENVVAR = "WIKIDB_PASSWORD"

BASE_PARAMS = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "",
    "password": "",
    "db": "wikidump",
    "cursorclass": pymysql.cursors.DictCursor
}


class DatabaseConnection(object):

    def __init__(self, db_params):
        self.db_params = dict(
            collections.ChainMap(BASE_PARAMS, db_params)
        )

        # Get username/password from env vars
        self.db_params["user"] = os.getenv(DB_USERNAME_ENVVAR)
        self.db_params["password"] = os.getenv(DB_PASSWORD_ENVVAR)

    def __enter__(self):
        self.connection = pymysql.connect(**self.db_params)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)

        return True

    def execute_query(self, query, params=(,)):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


class BaseQuerier(abc.ABC):
    """Base class for querying CloudSQL"""

    QUERY_STRING = ""

    def __init__(self, db_params=None):
        assert self.QUERY_STRING is not None
        db_params = {} if not db_params else db_params
        self.db_conn = DatabaseConnection(db_params)

    def execute_query(self, params=tuple()):
        with self.db_conn as db_conn:
            return self.db_conn.execute_query(
                self.QUERY_STRING,
                params=params
            )

    @abc.abstractmethod
    def get_payload(self, params=tuple()):
        return NotImplemented


class OutLinkFinder(BaseQuerier):

    QUERY_STRING = """
        SELECT
            gt_page_id AS from_node
            , gt_link_to_id AS to_node
        FROM
            page_links
        WHERE
            gt_page_id = %s
    """

    def get_payload(self, params=tuple()):
        results = self.execute_query(params)
        return [res.get("to_node") for res in results]


class InLinkFinder(BaseRequester):

    #
    # Query prameters are (node_id,)
    #

    QUERY_STRING = """
        SELECT
            gt_page_id AS from_node
            , gt_link_to_id AS to_node
        FROM
            page_links
        WHERE
            gt_link_to_id = %s
    """


class CategoryFinder(BaseRequester):
    QUERY_STRING = ""
    def get_payload(self, params=tuple()):
        results = self.execute_query(params)
        return [res.get("from_node") for res in results]


class NearbyFinder(BaseRequester):

    #
    # Query prameters are (lat, long, num_results)
    #

    QUERY_STRING = """
        SELECT
            gt_page_id
            , (
                POW(69.1 * (gt_lat - %s), 2) +
                POW(69.1 * (%s - gt_lon) * COS(gt_lon / 57.3), 2)
            ) AS distance_sqr
        FROM
            geo_tags
        ORDER BY distance_sqr ASC
        LIMIT %s;
    """

    def get_payload(self, params=tuple()):
        results = self.execute_query(params)
        return [res.get("gt_page_id") for res in results]
