## install stuff
# npm install dumpster-dip

cd /Users/mcmenamin/Repos/wikidump-parsing
mkdir ~/wiki/wikidump/


LANG=en  # af
DUMP_DATE=20240220

DUMP_HTTPS=https://dumps.wikimedia.org/${LANG}wiki/${DUMP_DATE}/
echo $DUMP_HTTPS

DUMP_GEOTAG_FILE=${LANG}wiki-${DUMP_DATE}-geo_tags.sql
DUMP_ARTICLE_FILE=${LANG}wiki-${DUMP_DATE}-pages-articles.xml


curl -L ${DUMP_HTTPS}/${DUMP_GEOTAG_FILE}.gz --output - | gzip -d > ~/wiki/wikidump/${DUMP_GEOTAG_FILE}
curl -L ${DUMP_HTTPS}/${DUMP_ARTICLE_FILE}.bz2 --output - | bzip2 -dc > ~/wiki/wikidump/${DUMP_ARTICLE_FILE}
