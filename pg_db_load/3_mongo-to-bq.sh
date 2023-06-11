LANG=en
DUMP_DATE=20230601

mongoexport \
    --host 127.0.0.1:27017 \
    -vv \
    --db "${LANG}wiki" \
    --collection "page_links" \
    --type "json" \
    --out ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl

gzip ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl

gsutil mv \
  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl.gz \
  gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl.gz


bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --max_bad_records=999999 \
    --ignore_unknown_values=true \
    --clustering_fields=page_id \
    --encoding=UTF-8 \
    --replace \
    --project_id tourguide-388723 \
    "pages.links" \
    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl.gz" \
    "page_links_bqschema.json"

bq update \
    --project_id tourguide-388723 \
    --clustering_fields page_id \
    pages.links