GRAPHIPEDIA_DIR=/Users/mcmenamin/GitHub/graphipedia/target
GRAPHIPEDIA_JAR=graphipedia-dataimport.jar
WIKI_DATA_DIR=/Users/mcmenamin/GitHub/wahipedia/neo4japp/graphdata

DUMP_DATE=20190101
WIKI_DUMP_FILE=enwiki-${DUMP_DATE}-pages-articles-multistream.xml.bz2


# Extract links from data dump
cd $GRAPHIPEDIA_DIR
bzip2 -dc $WIKI_DATA_DIR/$WIKI_DUMP_FILE | \
  java -classpath $GRAPHIPEDIA_JAR \
  org.graphipedia.dataimport.ExtractLinks \
  - \
  $WIKI_DATA_DIR/enwiki-links.xml

# Create Neo4J database
cd $GRAPHIPEDIA_DIR
java -Xmx3G -classpath $GRAPHIPEDIA_JAR \
  org.graphipedia.dataimport.neo4j.ImportGraph \
  $WIKI_DATA_DIR/enwiki-links.xml \
  /usr/local/var/neo4j/data/databases/wikidb

# neo4j start, run script to add degree features, clean redirects


neo4j-admin dump --database=wikidb --to=${WIKI_DATA_DIR}/wikidb.dump

gsutil cp ${WIKI_DATA_DIR}/wikidb.dump gs://coastal-epigram-162302.appspot.com/wikidump/${DUMP_DATE}/wikidb.dump
