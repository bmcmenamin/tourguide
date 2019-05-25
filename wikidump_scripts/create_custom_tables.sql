DROP TABLE IF EXISTS page_title_links; 
CREATE TABLE page_title_links (
   title varbinary(255) NOT NULL DEFAULT '',
   out_title varbinary(255) NOT NULL DEFAULT '',
   INDEX title_ix (title),
   INDEX out_title_ix (out_title)
);


INSERT INTO page_title_links
SELECT
    (SELECT page_title FROM page WHERE page_id = pl_from AND page_namespace = 0) AS title
    , pl_title AS out_title
FROM
    pagelinks
WHERE
    pl_namespace = 0
    AND pl_from_namespace = 0
;

DROP TABLE IF EXISTS page_degrees;
CREATE TABLE page_degrees (
   title varbinary(255) NOT NULL DEFAULT '',
   in_degree INT,
   out_degree INT,
   INDEX title_ix (title),
);


INSERT INTO page_degrees
SELECT
    title
    , COALESCE(id.in_degree, 0) AS in_degree
    , COALESCE(od.out_degree, 0) AS out_degree
FROM
    (
        SELECT
            title AS title
            , COUNT(DISTINCT(out_title)) AS out_degree
        FROM page_title_links
        GROUP BY title
    ) AS od
    LEFT JOIN
    (
        SELECT
            out_title AS title
            , COUNT(DISTINCT(title)) AS in_degree
        FROM page_title_links
        GROUP BY title
    ) AS id USING(title)
;