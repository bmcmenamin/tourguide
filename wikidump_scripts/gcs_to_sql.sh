# Copy wikipedia dumps from GCS to cloud sql

DUMPDATE=20190501

GEO_FILE=enwiki-${DUMPDATE}-geo_tags.sql
LINK_FILE=enwiki-${DUMPDATE}-pagelinks.sql
CATEGORY_FILE=enwiki-${DUMPDATE}-categorylinks.sql
REDIRECT_FILE=enwiki-${DUMPDATE}-redirect.sql
PAGES_FILE=enwiki-${DUMPDATE}-page.sql


ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
PROJECT_ID="$(gcloud config list --format 'value(core.project)' 2>/dev/null)"


DBNAME=wikidump${DUMPDATE}
SQLINSTANCE=wikidump


gcloud sql databases create ${DBNAME} --instance=${SQLINSTANCE}

for FILE in $REDIRECT_FILE $PAGES_FILE $CATEGORY_FILE $GEO_FILE $LINK_FILE 
do
    gcloud sql import sql \
        $SQLINSTANCE \
        gs://${PROJECT_ID}.appspot.com/wikidump/${FILE} \
        --quiet \
        --database=${DBNAME}
done
