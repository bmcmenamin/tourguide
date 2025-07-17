from typing import Optional, List

from google.cloud import bigquery
import pandas as pd



CREATE_UNDIRECTED_TABLE = """
DROP TABLE IF EXISTS pages.undirected_links;

CREATE TABLE pages.undirected_links
CLUSTER BY page_id AS 

WITH

in_links AS (
    SELECT
        page_id
        , in_link AS link
    FROM 
        `pages.links`
        , UNNEST(in_links) AS in_link
)

, out_links AS (
    SELECT
        page_id
        , out_link AS link
    FROM 
        `pages.links`
        , UNNEST(out_links) AS out_link
)

, unioned AS (
    SELECT page_id, link FROM in_links
    UNION ALL
    SELECT page_id, link FROM out_links
)

, agged AS (
    SELECT
        unioned.page_id
        , ARRAY_AGG(DISTINCT link) AS links
        , LOGICAL_OR(g.page_id IS NOT NULL) AS is_neighboring_geo
    FROM
        unioned
        LEFT JOIN `pages.geotags` AS g ON g.page_id = link
    GROUP BY
        page_id
)

SELECT
    agged.page_id
    , g.page_id IS NOT NULL AS is_geo
    , is_neighboring_geo
    , links
FROM
    agged
    LEFT JOIN `pages.geotags` AS g USING(page_id)
;
"""

QUERY_ALL_NEIGHBORS = """
SELECT DISTINCT
    link
FROM
    `pages.undirected_links`
    , UNNEST(links) AS link
WHERE
    page_id IN UNNEST(@nodes1)
"""




QUERY_ALL_TWOHOPS = """
WITH
pages.undirected_links
undir_links AS (
    SELECT
      page_id AS node_id
      , ARRAY_CONCAT(in_links, out_links) AS links
    FROM `pages.links`
)

, nodes_0 AS (
  SELECT 5828 AS node_id
)

, nodes_1 AS (
  SELECT DISTINCT
    node_id2
  FROM
    undir_links
    , UNNEST(links) AS node_id2
  WHERE
    node_id IN (SELECT * FROM nodes_0)
)

, nodes_2 AS (
  SELECT DISTINCT
    node_id2
  FROM
    undir_links
    , UNNEST(links) AS node_id2
  WHERE
    node_id IN (SELECT * FROM nodes_1)
)

, all_nodes AS (
  SELECT * FROM nodes_0
  UNION DISTINCT
  SELECT * FROM nodes_1
  UNION DISTINCT
  SELECT * FROM nodes_2
)


SELECT
  l.page_id
  , l.title
  , l.in_links
  , l.out_links
  , l.page_type
  , l.page_typeroot
  , l.is_disambig
  , STRUCT(
      g.lat
    , g.lon
    , g.dim
    , g.geog
  )
FROM
  all_nodes
  JOIN `pages.links` AS l ON node_id = page_id
  LEFT JOIN `pages.geotags` AS g USING(page_id)
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


def query_neighbors(bq: BigQueryInterface, nodes0: List[int]) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("nodes", "INT64", nodes0),
        ]
    )

    return bq.query(QUERY_ALL_NEIGHBORS, job_config=job_config)


def query_mutual(bq: BigQueryInterface, node: int) -> pd.DataFrame:

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("node", "FLOAT64", node)
        ]
    )

    return bq.query(QUERY_MUTUAL_LINKS, job_config=job_config)
