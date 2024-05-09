LANG=en
DUMP_DATE=20240220
mkdir ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split


mongoexport \
    --host 127.0.0.1:27017 \
    -vv \
    --db "${LANG}wiki" \
    --collection "page_links" \
    --type "json" \
    --out ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl

# split output into smaller files
split \
  -l 1000000 \
  -a 4 \
  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinks.jsonl \
  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinks_

for file in ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinks_*; do
    mv "$file" "$file.jsonl"
done

for file in ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinks_*.jsonl; do
    gzip $file
done

gsutil -m mv \
  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinks_*.jsonl.gz \
  gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}/parsedlinks/


bq load \
    --source_format=NEWLINE_DELIMITED_JSON \
    --max_bad_records=999999 \
    --ignore_unknown_values=true \
    --encoding=UTF-8 \
    --replace \
    --project_id tourguide-388723 \
    "pages.links" \
    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}/parsedlinks/*" \
    "page_links_bqschema.json"

bq update \
    --project_id tourguide-388723 \
    --clustering_fields page_id \
    pages.links





#mongoexport \
#    --host 127.0.0.1:27017 \
#    -vv \
#    --db "${LANG}wiki" \
#    --collection "links" \
#    --type "json" \
#    --out ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinktext.jsonl
#
## split output into smaller files
#split \
#  -l 1000000 \
#  -a 4 \
#  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_parsedlinktext.jsonl \
#  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinktext_
#
#for file in ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinktext_*; do
#    mv "$file" "$file.jsonl"
#done
#
#for file in ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinktext_*.jsonl; do
#    gzip $file
#done
#
#gsutil -m mv \
#  ~/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split/parsedlinktext_*.jsonl.gz \
#  gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}/parsedlinktext/
#
#bq load \
#    --source_format=NEWLINE_DELIMITED_JSON \
#    --max_bad_records=999999 \
#    --ignore_unknown_values=true \
#    --encoding=UTF-8 \
#    --replace \
#    --project_id tourguide-388723 \
#    "pages.linktext" \
#    "gs://tourguide-parsed/${LANG}wiki_${DUMP_DATE}/parsedlinktext/*" \
#    "page_linktext_bqschema.json"
#
#bq update \
#    --project_id tourguide-388723 \
#    --clustering_fields from_page_id \
#    --clustering_fields to_page_id \
#    pages.linktext
