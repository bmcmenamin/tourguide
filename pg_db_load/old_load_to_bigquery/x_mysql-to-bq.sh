LANG=en 
DUMP_DATE=20230520


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
WHERE gt_primary = 1
INTO OUTFILE '~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.json'
"

gzip ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.json

gsutil mv \
 ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_geotags.json.gz \
 gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_geotags.json.gz

bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --max_bad_records=999999 \
    --ignore_unknown_values=true \
    --encoding=UTF-8 \
    --replace \
    --project_id tourguide-388723 \
    "pages.geotags" \
    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_geotags.json.gz" \
    "geotags_bqschema.json"
