from typing import Optional, List

from google.cloud import bigquery
import pandas as pd


QUERY_EDGES = """
WITH edges AS (
    SELECT
        ARRAY_CONCAT(
            ARRAY(SELECT AS STRUCT il AS from_node, page_id AS to_node FROM UNNEST(in_links) AS il)
            , ARRAY(SELECT AS STRUCT page_id AS from_node, ol AS to_node FROM UNNEST(out_links) AS ol)
        ) AS edge_array
    FROM `pages.links`
    WHERE
        page_id IN UNNEST(@nodes)
        AND (num_in_links + num_out_links) > 1
)

SELECT DISTINCT
    e.from_node
    , e.to_node
FROM
    edges
    , UNNEST(edge_array) AS e
    JOIN `pages.links` AS l0 ON l0.page_id = e.from_node
    JOIN `pages.links` AS l1 ON l1.page_id = e.to_node
WHERE
    (l0.num_in_links + l0.num_out_links) > 1
    AND (l1.num_in_links + l1.num_out_links) > 1
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
WITH nested_neighbors AS (
    SELECT
        page_id
        , ARRAY_CONCAT(in_links, out_links) AS new_edges
    FROM `pages.links`
    WHERE
        page_id IN UNNEST(@nodes)
)

, neighbors AS (
    SELECT
        n.page_id AS geo_page_id
        , e AS new_page_id
    FROM
        nested_neighbors AS n
        , UNNEST(new_edges) AS e
        JOIN `pages.links` AS l ON e = l.page_id
    WHERE
        l.num_in_links < @max_in_degree
        AND l.has_place_category
)

SELECT
    new_page_id AS page_id
FROM neighbors
GROUP BY new_page_id
HAVING COUNT(DISTINCT geo_page_id) > 1
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
            bigquery.ScalarQueryParameter("max_in_degree", "INT64", 2000)
        ]
    )

    return bq.query(QUERY_NEARBY_EXTENDED, job_config=job_config)


