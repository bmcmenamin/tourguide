DELETE
FROM
  page
WHERE
  page_namespace <> 0


DELETE
FROM
  pagelinks
WHERE
  NOT (pl_from_namespace = 0 AND pl_namespace = 0)
;

