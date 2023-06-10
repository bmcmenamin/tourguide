//in another terminal, run: brew services start mongodb-community

import dumpster from 'dumpster-dive'

const lang =  'en'; // 'af';  // 
const dumpdate = 20230601;
const working_dir = '/Users/mcmenamin/wiki/'
const path_to_file = `${working_dir}/wikidump/${lang}wiki-${dumpdate}-pages-articles.xml`
//const path_to_file = `${working_dir}/wikidump/enwiki-tmp.xml`


function parseLinks(doc) {

  const badSectionNames = [
      'Notes',
      'References',
      'External links'
  ]

  const placeTokens = [
      'town',
      'towns',
      'city',
      'cities',
      'county',
      'counties',
      'country',
      'countries',
      'municipality',
      'municipalities',
      'region',
      'regions',
      'place',
      'places',
      'location',
      'locations',
  ]


  var output = {
    'title': Buffer.from(doc.title(), 'utf-8').toString(),
    'pageID': doc.pageID(),
  }

  const redirectLinks = (
      [doc.redirectTo()]
      .filter(s => s !== null)
      .filter(s => typeof s === 'object')
      .filter(s => 'page' in s)
      .filter(s => s.page != doc.title())
      .map(s => s.page)
  )

  const sectionLinks = (
      doc.sections()
      .filter(s => !badSectionNames.includes(s.name))
      .flatMap(s => s.links())
      .filter(l => l.json().type == 'internal')
      .map(l => l.json().page)
  )

  const infoboxLinks = (
      doc.infoboxes()
      .flatMap(i => i.links())
      .filter(l => l.json().type == 'internal')
      .map(l => l.json().page)
  )

  const outlinks = [...new Set([...redirectLinks, ...sectionLinks, ...infoboxLinks])]
  output['outlinks'] = outlinks.map(s => Buffer.from(s, 'utf-8').toString())


  const catTokens = (
      doc.categories()
      .map(s => Buffer.from(s, 'utf-8').toString())
      .flatMap(s => s.toLowerCase().split(/\b\s+(?!$)/))
  )

  output['has_place_category'] = catTokens.some(v => placeTokens.includes(v))

  return output

}


process.chdir(working_dir);

dumpster({
  file: path_to_file,
  db: `${lang}wiki`,
  skip_redirects: false,
  skip_disambig: false,
  //workers: 1,
  batch_size: 1000,
  custom: parseLinks
});

