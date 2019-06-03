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
    "db": "wiki-20190501",
    #"cursorclass": pymysql.cursors.DictCursor
}


class DatabaseConnection(object):

    def __init__(self, db_params):
        self.db_params = dict(
            collections.ChainMap(BASE_PARAMS, db_params)
        )

        # Get username/password from env vars
        self.db_params["user"] = 'root' #os.getenv(DB_USERNAME_ENVVAR)
        self.db_params["password"] = 'strider' #os.getenv(DB_PASSWORD_ENVVAR)

    def __enter__(self):
        self.connection = pymysql.connect(**self.db_params)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.connection.close()
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
        return True

    def execute(self, query, params=tuple()):
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
        return []


class BaseQuerier(abc.ABC):
    """Base class for querying CloudSQL"""

    QUERY_STRING = ""

    def __init__(self, db_params=None):
        assert self.QUERY_STRING is not None
        db_params = {} if not db_params else db_params
        self.db_conn = DatabaseConnection(db_params)

    def execute_query(self, params=tuple()):
        with self.db_conn as db_conn:
            return self.db_conn.execute(
                self.QUERY_STRING,
                params=params
            )

    @abc.abstractmethod
    def get_payload(self, params=tuple()):
        return NotImplemented


class OutLinkFinder(BaseQuerier):

    #
    # Find outgoing links, NOT resolving redirects
    # Query parameters are (node_names,)
    #

    QUERY_STRING = """
        SELECT
            pl_from AS page_title
            , page_id AS out_page_title
        FROM
            pagelinks AS pl 
            JOIN page ON page_title=pl_title
        WHERE
            pl_from IN %(nodes)s
            AND page_namespace = 0
            AND pl_namespace = 0
            AND pl_from_namespace = 0
            AND page_title NOT LIKE "List_%%"
            AND pl_title NOT LIKE "List_%%"
        ;
    """
    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)
        return results


class InLinkFinder(BaseQuerier):

    #
    # Find incoming links, but NOT resolving redirects
    # Query parameters are (node_names,)
    #

    QUERY_STRING = """
        SELECT DISTINCT
            pl_from AS page_title
            , page_id AS out_page_title
        FROM
            page 
            JOIN pagelinks ON page_title=pl_title
        WHERE
            page_id IN %(nodes)s
            AND pl_namespace = 0
            AND pl_from_namespace = 0
            AND page_title NOT LIKE "List_%%"
            AND pl_title NOT LIKE "List_%%"
        ;
    """

    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)
        return results


class NodeAttributeFinder(BaseQuerier):

    #
    # Find attributes of nodes
    # Query parameters are (node_names,)
    #

    QUERY_STRING = """
        SELECT
            page_id
            , COALESCE(id.in_degree, 0) AS in_degree
            , COALESCE(od.out_degree, 0) AS out_degree
        FROM
            (
                SELECT
                    pl_from AS page_id
                    , COUNT(DISTINCT(pl_title)) AS out_degree
                FROM
                    pagelinks
                WHERE
                    pl_from IN %(nodes)s
                    AND pl_namespace = 0
                    AND pl_from_namespace = 0
                GROUP BY pl_from
            ) AS od
            LEFT JOIN
            (
                SELECT
                    COUNT(DISTINCT(pl_from)) AS in_degree
                    , page_id
                FROM
                    page
                    JOIN pagelinks ON page_title = pl_title
                WHERE
                    page_id IN %(nodes)s
                    AND pl_namespace = 0
                    AND pl_from_namespace = 0
                GROUP BY page_id
            ) AS id USING(page_id)
        ;
    """
    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)
        return results

class CategoryFinder(BaseQuerier):

    #
    # Get categories for a node
    # Query parameters are (node_name,)
    #
    
    QUERY_STRING = """
        SELECT DISTINCT
            cl_from AS page_title
            , cl_to AS cat_name
        FROM
            categorylinks
        WHERE
            cl_from IN %(nodes)s
            AND cl_type = "page"
        ;
    """
    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)

        output_dict = collections.defaultdict(list)
        for res in results:
            n = res[0]
            c = res[1]
            output_dict[n].append(c)

        return dict(output_dict)


class CityFinder(BaseQuerier):

    #
    # Get names of nearby cities
    # Query prameters are (lat, long, num_results)
    #

    QUERY_STRING = """
        SELECT DISTINCT
            gt_page_id AS page_title
            , MIN(
                POW(69.1 * (gt_lat - %(lat)s), 2) +
                POW(69.1 * (%(lon)s - gt_lon) * COS(gt_lon / 57.3), 2)
            ) AS distance_sqr
        FROM
            geo_tags
        WHERE
            gt_lat BETWEEN
                %(lat)s - (18 / 69.1) AND %(lat)s + (18 / 69.1)

            AND gt_lon BETWEEN
                %(lon)s - (18 / (69.1 * COS(%(lat)s)))
                AND %(lon)s + (18 / (69.1 * COS(%(lat)s)))

            AND EXISTS (
                SELECT 1
                FROM categorylinks
                WHERE cl_to LIKE "Cities%%" AND cl_from=gt_page_id
            )
        GROUP BY page_title
        ORDER BY distance_sqr ASC
        LIMIT %(n)s;
    """
    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)
        return [
            res[0] for res in results
        ]

class NearbyFinder(BaseQuerier):

    #
    # Get names of nearby things
    # Query prameters are (lat, long, num_results)
    #

    QUERY_STRING = """
        SELECT DISTINCT
            gt_page_id AS page_title
            , MIN(
                POW(69.1 * (gt_lat - %(lat)s), 2) +
                POW(69.1 * (%(lon)s - gt_lon) * COS(gt_lon / 57.3), 2)
            ) AS distance_sqr
        FROM
            geo_tags
        WHERE
            gt_lat BETWEEN
                %(lat)s - (18 / 69.1) AND %(lat)s + (18 / 69.1)

            AND gt_lon BETWEEN
                %(lon)s - (18 / (69.1 * COS(%(lat)s)))
                AND %(lon)s + (18 / (69.1 * COS(%(lat)s)))

            AND NOT EXISTS (
                SELECT 1
                FROM categorylinks
                WHERE cl_to LIKE "Cities%%" AND cl_from=gt_page_id
            )
        GROUP BY page_title
        ORDER BY distance_sqr ASC
        LIMIT %(n)s;
    """

        #JOIN page ON page_id = gt_page_id
        #AND page_namespace = 0
        #AND page_title NOT LIKE "List_%%"

    def get_payload(self, params=tuple()):
        results = self.execute_query(params=params)
        return [
            res[0] for res in results
        ]
