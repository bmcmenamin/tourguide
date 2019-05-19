# Copy wikipedia dumps from wiki -> compute instance -> GCS

# Mount external disk
#sudo lsblk
sudo mkfs.ext4 -m 0 -F -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb
sudo mkdir -p /mountdisk
sudo mount -o discard,defaults /dev/sdb /mountdisk
sudo chmod a+w /mountdisk


DUMPDATE=20190501

ACCESS_TOKEN="$(gcloud auth application-default print-access-token)"
PROJECT_ID="$(gcloud config list --format 'value(core.project)' 2>/dev/null)"


WIKI_BASE_URL=http://dumps.wikimedia.your.org/enwiki
LOCAL_DIR=/mountdisk/enwiki/${DUMPDATE}


GEO_FILE=enwiki-${DUMPDATE}-geo_tags.sql
LINK_FILE=enwiki-${DUMPDATE}-pagelinks.sql
CATEGORY_FILE=enwiki-${DUMPDATE}-categorylinks.sql
REDIRECT_FILE=enwiki-${DUMPDATE}-redirect.sql
PAGES_FILE=enwiki-${DUMPDATE}-page.sql


sudo mkdir -p ${LOCAL_DIR}
sudo chmod -R 777 ${LOCAL_DIR}
cd ${LOCAL_DIR}

for FILE in $PAGES_FILE $GEO_FILE $LINK_FILE $CATEGORY_FILE $REDIRECT_FILE
do
    curl ${WIKI_BASE_URL}/${DUMPDATE}/${FILE}.gz > ${LOCAL_DIR}/${FILE}.gz
    gunzip ${LOCAL_DIR}/${FILE}.gz
    gsutil cp ${LOCAL_DIR}/${FILE} gs://${PROJECT_ID}.appspot.com/wikidump/${FILE}
    rm ${LOCAL_DIR}/${FILE}
done

