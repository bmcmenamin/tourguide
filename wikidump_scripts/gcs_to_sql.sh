# Copy wikipedia dumps from GCS to cloud sql

DUMPDATE=20190501

GEO_FILE=enwiki-${DUMPDATE}-geo_tags.sql
LINK_FILE=enwiki-${DUMPDATE}-pagelinks.sql
CATEGORY_FILE=enwiki-${DUMPDATE}-categorylinks.sql
REDIRECT_FILE=enwiki-${DUMPDATE}-redirect.sql
PAGES_FILE=enwiki-${DUMPDATE}-page.sql


ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
PROJECT_ID="$(gcloud config list --format 'value(core.project)' 2>/dev/null)"


DBNAME=wiki-${DUMPDATE}
SQLINSTANCE=bmcdb


gcloud sql databases create ${DBNAME} --instance=${SQLINSTANCE}


gcloud sql import sql \
    $SQLINSTANCE \
    gs://${PROJECT_ID}.appspot.com/wikidump/${GEO_FILE} \
    --quiet \
    --database=${DBNAME}

gcloud sql import sql \
    $SQLINSTANCE \
    gs://${PROJECT_ID}.appspot.com/wikidump/${REDIRECT_FILE} \
    --quiet \
    --database=${DBNAME}

gcloud sql import sql \
    $SQLINSTANCE \
    gs://${PROJECT_ID}.appspot.com/wikidump/${PAGES_FILE} \
    --quiet \
    --database=${DBNAME}

gcloud sql import sql \
    $SQLINSTANCE \
    gs://${PROJECT_ID}.appspot.com/wikidump/${CATEGORY_FILE} \
    --quiet \
    --database=${DBNAME}

gcloud sql import sql \
    $SQLINSTANCE \
    gs://${PROJECT_ID}.appspot.com/wikidump/${LINK_FILE} \
    --quiet \
    --database=${DBNAME}
