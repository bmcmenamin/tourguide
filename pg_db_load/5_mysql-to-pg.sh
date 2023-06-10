LANG=en 
DUMP_DATE=20230601
HOST_IP_PG=34.133.168.166

JSONL_FILE="/Users/mcmenamin/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.jsonl"

rm -f ${JSONL_FILE}

mysql -u root enwiki -e "
SELECT JSON_OBJECT
    (
        'page_id', gt_page_id,
        'lat', gt_lat,
        'lon', gt_lon,
        'dim', gt_dim
    )
FROM geo_tags
WHERE
    gt_primary = 1
    AND gt_globe = 0x6561727468
INTO OUTFILE '${JSONL_FILE}'
"

psql -U postgres -p 5432 -h ${HOST_IP_PG} -c "CREATE DATABASE ${LANG}wiki;"
psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    DROP TABLE IF EXISTS geotags;
    CREATE TABLE geotags (
        page_id INT,
        lat FLOAT,
        lon FLOAT,
        dim INT
    );
    CREATE INDEX lat_idx ON geotags USING BTREE (lat);
    CREATE INDEX lon_idx ON geotags USING BTREE (lon);
"

psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    DROP TABLE IF EXISTS temp_pg;
    CREATE TABLE temp_pg (data jsonb);
"


echo "\COPY temp_pg from '${JSONL_FILE}';" | psql -U postgres -p 5432 -h ${HOST_IP_PG} enwiki
psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    TRUNCATE geotags;
    INSERT INTO geotags (page_id, lat, lon, dim)
    SELECT
        CAST(data->>'page_id' AS INT)
        , CAST(data->>'lat' AS FLOAT)
        , CAST(data->>'lon' AS FLOAT)
        , CAST(data->>'dim' AS INT)
    FROM temp_pg;
    DROP TABLE temp_pg;
"

rm -f ${JSONL_FILE}

