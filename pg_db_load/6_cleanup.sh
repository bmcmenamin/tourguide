LANG=en
DUMP_DATE=20230601

# drop dump files
rm -f /Users/mcmenamin/wiki/wikidump/${LANG}wiki-${DUMP_DATE}-*

# Drop mongo DB
mongosh --eval "use ${LANG}wiki; db.dropDatabase()"

# Drop mysql DB
mysql -u root -c "DROP DATABASE ${LANG}wiki;"
