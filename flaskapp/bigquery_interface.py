from typing import Optional, List

from google.cloud import bigquery
import pandas as pd


S2_CELL_SIZE = 14


CREATE_S2_TABLE = """
DROP TABLE IF EXISTS pages.s2cells;

CREATE TABLE pages.s2cells AS 

-- cell sizes reference https://s2geometry.io/resources/s2cell_statistics
WITH
cells AS (
    SELECT
        S2_CELLIDFROMPOINT(geog, @s2_cell_size) AS cell_id
        , ST_CENTROID_AGG(geog) AS cell_centroid
        , ARRAY_AGG(DISTINCT page_id) AS geo_page_ids
        , COUNT(DISTINCT page_id) AS num_geo_page_ids
    FROM 
        `pages.geotags`
        JOIN `pages.links` USING(page_id)
    WHERE
        UPPER(title) NOT LIKE "LIST OF %"
        AND page_typeroot IS NOT NULL
        AND NOT is_disambig
    GROUP BY
        cell_id
)

, _extended AS (
    SELECT
        cell_id
        , num_geo_page_ids
        , geo_page_id
        , extended_page_id
    FROM
        cells
        ,UNNEST(geo_page_ids) AS geo_page_id
        JOIN `pages.links` AS l0 ON geo_page_id=l0.page_id
        , UNNEST(ARRAY_CONCAT(l0.in_links, l0.out_links)) AS extended_page_id
        JOIN `pages.links` AS l1 ON l1.page_id = extended_page_id
        LEFT JOIN `pages.geotags` AS gt ON l1.page_id = gt.page_id
    WHERE
        l1.page_typeroot = "Place"
        AND COALESCE(l1.page_type, "Place") <> "Place"
        AND gt.page_id IS NULL
        AND UPPER(l1.title) NOT LIKE "LIST OF %"
        AND NOT l1.is_disambig
)

, extended AS (
    SELECT
        cell_id
        , ARRAY_AGG(extended_page_id) AS extended_page_ids
    FROM (
        SELECT
            cell_id
            , extended_page_id
        FROM _extended
        GROUP BY cell_id, extended_page_id
        HAVING COUNT(DISTINCT geo_page_id) > (0.5 * MAX(num_geo_page_ids))
    )
    GROUP BY cell_id
)

SELECT
    cell_id
    , cell_centroid
    , geo_page_ids
    , extended_page_ids
FROM
    cells
    LEFT JOIN extended USING(cell_id)
;
"""


QUERY_NEARBY = """
SELECT DISTINCT
    page_id
    , title
    , num_in_links
    , num_out_links
FROM
    pages.s2cells
    , UNNEST(ARRAY_CONCAT(geo_page_ids, extended_page_ids)) AS page_id
    JOIN pages.links USING(page_id)
WHERE
    cell_id = S2_CELLIDFROMPOINT(ST_GEOGPOINT(@lon, @lat), @s2_cell_size) 
"""


QUERY_BRIDGES = """
SELECT
    page_id
    , title
    , page_type
    , page_typeroot
    , num_in_links
    , num_out_links
    , ARRAY((SELECT ol FROM UNNEST(out_links) AS ol WHERE ol IN UNNEST(@nodes0))) AS links0
    , ARRAY((SELECT ol FROM UNNEST(out_links) AS ol WHERE ol IN UNNEST(@nodes1))) AS links1
FROM
    `pages.links`
WHERE
    NOT is_disambig
    AND page_typeroot IS NOT NULL
    AND EXISTS((SELECT 1 FROM UNNEST(out_links) AS ol WHERE ol IN UNNEST(@nodes0)))
    AND EXISTS((SELECT 1 FROM UNNEST(out_links) AS ol WHERE ol IN UNNEST(@nodes1)))
    --AND page_id NOT IN UNNEST(@nodes0)
    AND page_id NOT IN UNNEST(@nodes1)
"""


QUERY_MUTUAL_LINKS = """

SELECT
    l0.page_id
    , l0.title
    , l0.page_type
    , l0.page_typeroot
    , l0.num_in_links
    , l0.num_out_links
FROM
  pages.links AS l0
WHERE
  l0.page_id = @node

UNION DISTINCT

SELECT
    l1.page_id
    , l1.title
    , l1.page_type
    , l1.page_typeroot
    , l1.num_in_links
    , l1.num_out_links
FROM
  pages.links AS l0
  , UNNEST(out_links) AS out_link
  JOIN pages.links AS l1 ON out_link=l1.page_id
WHERE
  l0.page_id = @node
  AND EXISTS((SELECT 1 FROM UNNEST(l1.out_links) AS ol WHERE ol = @node))
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


def create_s2_table(bq: BigQueryInterface) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("s2_cell_size", "INT64", S2_CELL_SIZE),
            bigquery.ScalarQueryParameter("max_in_degree", "INT64", 1000),
            bigquery.ScalarQueryParameter("max_out_degree", "INT64", 1000)
        ]
    )

    return bq.query(CREATE_S2_TABLE, job_config=job_config)


def query_nearby(bq: BigQueryInterface, lat: float, lon: float) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("lat", "FLOAT64", lat),
            bigquery.ScalarQueryParameter("lon", "FLOAT64", lon),
            bigquery.ScalarQueryParameter("s2_cell_size", "INT64", S2_CELL_SIZE),
        ]
    )

    return bq.query(QUERY_NEARBY, job_config=job_config)


def query_bridges(bq: BigQueryInterface, nodes0: List[int], nodes1: List[int]) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes0", "INT64", nodes0),
            bigquery.ArrayQueryParameter("nodes1", "INT64", nodes1),
        ]
    )

    return bq.query(QUERY_BRIDGES, job_config=job_config)


def query_mutual(bq: BigQueryInterface, node: int) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("node", "FLOAT64", node)
        ]
    )

    return bq.query(QUERY_MUTUAL_LINKS, job_config=job_config)
