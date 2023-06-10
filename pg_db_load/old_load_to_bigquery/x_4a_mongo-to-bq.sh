LANG=en  # af
DUMP_DATE=20230520

mongoexport \
    --host 127.0.0.1:27017 \
    -vv \
    --db "${LANG}wiki" \
    --collection "page_links" \
    --type "json" \
    --out ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.json

gzip ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.json

gsutil mv \
  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.json.gz \
  gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_parsedlinks.json.gz


bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --max_bad_records=999999 \
    --ignore_unknown_values=true \
    --encoding=UTF-8 \
    --replace \
    --project_id tourguide-388723 \
    "pages.links" \
    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_parsedlinks.json.gz" \
    "page_links_bqschema.json"
