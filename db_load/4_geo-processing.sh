LANG=en
DUMP_DATE=20230601

DUMP_GEOTAG_FILE=${LANG}wiki-${DUMP_DATE}-geo_tags.sql

mysql -u root -e "CREATE DATABASE enwiki;"
mysql -u root enwiki < ~/wiki/wikidump/${DUMP_GEOTAG_FILE}
