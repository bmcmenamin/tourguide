# Copy wikipedia dumps from GCS to cloud sql

DUMPDATE=20190501

GEO_FILE=enwiki-${DUMPDATE}-geo_tags.sql
LINK_FILE=enwiki-${DUMPDATE}-pagelinks.sql

ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
PROJECT_ID="$(gcloud config list --format 'value(core.project)' 2>/dev/null)"

DBNAME=wikidump${DUMPDATE}
SQLINSTANCE=wikidump

gcloud sql databases create ${DBNAME} --instance=${SQLINSTANCE}

gcloud sql import sql \
    $SQLINSTANCE gs://${PROJECT_ID}.appspot.com/wikidump/${GEO_FILE} \
    --database=${DBNAME}

gcloud sql import sql \
    $SQLINSTANCE gs://${PROJECT_ID}.appspot.com/wikidump/${LINK_FILE} \
    --database=${DBNAME}