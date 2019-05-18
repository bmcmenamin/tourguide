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


sudo mkdir -p ${LOCAL_DIR}
sudo chmod -R 777 ${LOCAL_DIR}
cd ${LOCAL_DIR}

curl ${WIKI_BASE_URL}/${DUMPDATE}/${GEO_FILE}.gz > ${LOCAL_DIR}/${GEO_FILE}.gz
curl ${WIKI_BASE_URL}/${DUMPDATE}/${LINK_FILE}.gz > ${LOCAL_DIR}/${LINK_FILE}.gz

gunzip ${LOCAL_DIR}/${GEO_FILE}.gz
gsutil cp ${LOCAL_DIR}/${GEO_FILE} gs://${PROJECT_ID}.appspot.com/wikidump/${GEO_FILE}
rm ${LOCAL_DIR}/${GEO_FILE}

gunzip ${LOCAL_DIR}/${LINK_FILE}.gz
gsutil cp ${LOCAL_DIR}/${LINK_FILE} gs://${PROJECT_ID}.appspot.com/wikidump/${LINK_FILE}
rm ${LOCAL_DIR}/${LINK_FILE}
