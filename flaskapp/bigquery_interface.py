from typing import Optional, List

from google.cloud import bigquery
import pandas as pd


QUERY_EDGES = """
WITH edges AS (
    SELECT
        ARRAY(
            SELECT AS STRUCT
                page_id AS from_node
                , ol AS to_node
            FROM UNNEST(out_links) AS ol
            WHERE ol IN UNNEST(@nodes)
        ) AS edge_array
    FROM `pages.links`
    WHERE
        page_id IN UNNEST(@nodes)
)

SELECT DISTINCT
    e.from_node
    , e.to_node
FROM
    edges
    , UNNEST(edge_array) AS e
"""


QUERY_NEIGHBORS = """
WITH

current_nodes AS (
    SELECT
        page_id
        , CASE
            WHEN num_in_links < @max_in_degree THEN in_links
            ELSE []
            END AS in_links
        , CASE
            WHEN num_out_links < @max_out_degree THEN out_links
            ELSE []
            END AS out_links
    FROM
        `pages.links`
    WHERE
        page_id IN UNNEST(@nodes)
)

, new_neighbors AS (
    SELECT DISTINCT
        new_page_id AS page_id
    FROM
        current_nodes
        , UNNEST(ARRAY_CONCAT(in_links, out_links)) AS new_page_id
    WHERE
        new_page_id NOT IN UNNEST(@nodes)
)

SELECT
    page_id
    , title
    , has_place_category
    , num_in_links
    , num_out_links
    , num_in_links + num_out_links AS degree
FROM
    `pages.links`
    JOIN new_neighbors USING(page_id)
"""


QUERY_NODES = """
SELECT
    page_id
    , title
    , has_place_category
    , num_in_links
    , num_out_links
    , num_in_links + num_out_links AS degree
FROM `pages.links`
WHERE page_id IN UNNEST(@nodes)
"""


QUERY_NEARBY = """
WITH dists AS (
    SELECT
        gt.page_id
        , ST_DISTANCE(geog, ST_GEOGPOINT(@lon, @lat)) AS d
    FROM pages.geotags AS gt
    WHERE ST_WITHIN(geog, ST_BUFFER(ST_GEOGPOINT(@lon, @lat), 10000 / 2))
)

SELECT page_id
FROM dists
QUALIFY ROW_NUMBER() OVER (ORDER BY d ASC) <= @num_to_keep;
"""


QUERY_NEARBY_EXTENDED = """
WITH new_neighbors AS (
    SELECT
        page_id AS orig_page_id
        , new_page_id
    FROM
        `pages.links`
        , UNNEST(ARRAY_CONCAT(in_links, out_links)) AS new_page_id
    WHERE
        page_id IN UNNEST(@nodes)
        AND new_page_id NOT IN UNNEST(@nodes)
)

, filtered_neighbors AS (
    SELECT
        orig_page_id
        , new_page_id
    FROM
        new_neighbors AS n
        JOIN `pages.links` AS l ON l.page_id = new_page_id
        LEFT JOIN `pages.geotags` AS gt ON gt.page_id = new_page_id
    WHERE
        (l.has_place_category OR gt.page_id IS NOT NULL)
        AND l.num_in_links < @max_in_degree
        AND l.num_out_links < @max_out_degree
)

SELECT
    new_page_id AS page_id
FROM filtered_neighbors
GROUP BY new_page_id
HAVING COUNT(DISTINCT orig_page_id) > 1
"""


class BigQueryInterface(object):

    def __enter__(self):
        self.client = bigquery.Client(project=self.project_id)
        return self

    def __exit__(self, type, value, tb):
        self.client.close()

    def __init__(self, project_id: str):
        self.client: Optional[bigquery.Client] = None
        self.project_id = project_id

    def query(self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None) -> pd.DataFrame:
        query_job = self.client.query(query, job_config=job_config)
        return pd.DataFrame([dict(row.items()) for row in query_job])


def query_nodes(bq: BigQueryInterface, nodes: List[int]) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes", "INT64", nodes)
        ]
    )

    return bq.query(QUERY_NODES, job_config=job_config)


def query_edges(bq: BigQueryInterface, nodes: List[int]) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes", "INT64", nodes),
            bigquery.ScalarQueryParameter("max_degree", "INT64", 10_000),
        ]
    )

    return bq.query(QUERY_EDGES, job_config=job_config)


def query_nearby(bq: BigQueryInterface, lat: float, lon: float, num_to_keep: Optional[int] = 15) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("num_to_keep", "INT64", num_to_keep),
            bigquery.ScalarQueryParameter("lat", "FLOAT64", lat),
            bigquery.ScalarQueryParameter("lon", "FLOAT64", lon)
        ]
    )

    return bq.query(QUERY_NEARBY, job_config=job_config)


def query_nearby_extended(bq: BigQueryInterface, nodes: List[int]) -> pd.DataFrame:
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes", "INT64", nodes),
            bigquery.ScalarQueryParameter("max_in_degree", "INT64", 1000),
            bigquery.ScalarQueryParameter("max_out_degree", "INT64", 1000)
        ]
    )

    return bq.query(QUERY_NEARBY_EXTENDED, job_config=job_config)


def query_neighbors(bq: BigQueryInterface, nodes: List[int]) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes", "INT64", nodes),
            bigquery.ScalarQueryParameter("max_in_degree", "INT64", 1000),
            bigquery.ScalarQueryParameter("max_out_degree", "INT64", 1000)
        ]
    )

    return bq.query(QUERY_NEIGHBORS, job_config=job_config)

