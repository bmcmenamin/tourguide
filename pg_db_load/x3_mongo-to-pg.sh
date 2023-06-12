LANG=en
DUMP_DATE=20230601

HOST_IP_PG=34.133.168.166



rm -f ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_pagelinks.jsonl

mongoexport \
    --host 127.0.0.1:27017 \
    -vv \
    --db "${LANG}wiki" \
    --collection "page_links" \
    --type "json" \
    --out ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_pagelinks.jsonl


# split file
sed 's/\\/\\\\/g' ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_pagelinks.jsonl \
  | split -l 100000 - ~/wiki/wikidump/pagelinks-

psql -U postgres -p 5432 -h ${HOST_IP_PG} -c "CREATE DATABASE ${LANG}wiki;"

psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    DROP TABLE IF EXISTS temp_pl;
    CREATE TABLE temp_pl (data jsonb);
"

for file in ~/wiki/wikidump/pagelinks-*; do
  echo "\COPY temp_pl from '${file}';" | psql -U postgres -p 5432 -h ${HOST_IP_PG} enwiki
done

psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    SELECT COUNT(1) FROM temp_pl;
"


psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "

    DROP TABLE IF EXISTS pagelinks;
    CREATE TABLE pagelinks (
        page_id INT
        , title TEXT
        , has_place_category BOOL
        , in_links INT[]
        , out_links INT[]
        , num_in_links INT
        , num_out_links INT
    );
    CREATE INDEX page_id_idx ON pagelinks USING BTREE (page_id);

    CREATE OR REPLACE FUNCTION jsonb_array_to_int_array(_js jsonb)
      RETURNS INT[]
      LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE AS
    'SELECT ARRAY(SELECT JSONB_ARRAY_ELEMENTS_TEXT(_js))::INT[]';

    TRUNCATE pagelinks;
    INSERT INTO pagelinks (page_id, title, has_place_category, in_links, out_links, num_in_links, num_out_links)
    SELECT
        CAST(data->>'page_id' AS INT)
        , CAST(data->>'title' AS TEXT)
        , CAST(data->>'has_place_category' AS BOOL)
        , jsonb_array_to_int_array(data->'in_links')
        , jsonb_array_to_int_array(data->'out_links')
        , CAST(data->>'num_in_links' AS INT)
        , CAST(data->>'num_out_links' AS INT)
    FROM temp_pl;
    DROP TABLE temp_pl;
"

psql -U postgres -p 5432 -h ${HOST_IP_PG} ${LANG}wiki -c "
    SELECT COUNT(1) FROM pagelinks;
"


rm -f ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_pagelinks.jsonl
rm -f ~/wiki/wikidump/pagelinks-*
