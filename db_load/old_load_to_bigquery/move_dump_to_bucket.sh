# https://dumps.wikimedia.org/enwiki/20211020/
# coastal-epigram-162302

#cd /home/bmcmenamin

cd /Users/mcmenamin/GitHub/wikidump-parsing

DUMP_DATE=20211020
DUMP_HTTPS=https://dumps.wikimedia.org/enwiki/${DUMP_DATE}/

DUMP_SUFFIX=p1p41242
DUMP_GEOTAG_FILE=enwiki-${DUMP_DATE}-geo_tags.sql
DUMP_REDIRECT_FILE=enwiki-${DUMP_DATE}-redirect.sql
DUMP_ARTICLE_FILE=enwiki-${DUMP_DATE}-pages-articles1.xml-${DUMP_SUFFIX}


GCS_DUMP_BUCKET=wikidump

curl -L ${DUMP_HTTPS}/${DUMP_GEOTAG_FILE}.gz --output - | gzip -d | gsutil cp - gs://${GCS_DUMP_BUCKET}/${DUMP_GEOTAG_FILE}
curl -L ${DUMP_HTTPS}/${DUMP_REDIRECT_FILE}.gz --output - | gzip -d | gsutil cp - gs://${GCS_DUMP_BUCKET}/${DUMP_REDIRECT_FILE}
curl -L ${DUMP_HTTPS}/${DUMP_ARTICLE_FILE}.bz2 --output - | bzip2 -dc > ${DUMP_ARTICLE_FILE}
