LANG=en
DUMP_DATE=20240220

# drop dump files
rm -f /Users/mcmenamin/wiki/wikidump/${LANG}wiki-${DUMP_DATE}-*
rm -f /Users/mcmenamin/wiki/wikidump/${LANG}wiki_${DUMP_DATE}_split

# Drop mongo DB
mongosh --eval "use ${LANG}wiki; db.dropDatabase()"

# Drop mysql DB
mysql -u root -c "DROP DATABASE ${LANG}wiki;"
