LANG=en 
DUMP_DATE=20240501


rm -f ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.json

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
INTO OUTFILE '~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.jsonl'
"

gzip ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.jsonl

gsutil mv \
 ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.jsonl.gz \
 gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_geotags.jsonl.gz

bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --max_bad_records=999999 \
    --ignore_unknown_values=true \
    --encoding=UTF-8 \
    --replace \
    --project_id tourguide-388723 \
    "pages.geotags" \
    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_geotags.jsonl.gz" \
    "geotags_bqschema.json"


bq query \
    --project_id tourguide-388723 \
    --nouse_legacy_sql \
    'ALTER TABLE `pages.geotags` ADD COLUMN geog GEOGRAPHY;'

bq query \
    --project_id tourguide-388723 \
    --nouse_legacy_sql \
    'UPDATE `pages.geotags` SET geog = ST_GEOGPOINT(lon, lat) WHERE TRUE;'

bq update \
    --project_id tourguide-388723 \
    --clustering_fields geog \
    pages.geotags
