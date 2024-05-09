//in another terminal, run: brew services start mongodb-community
// node ./1_parse-script.js

import dumpster from 'dumpster-dive'

// in the file ./node_modules/dumpster-dive/src/worker/02-parseWiki.js, add 
// this to imports to use plugins:
//   const wtfClassify = require('wtf-plugin-classify');
//   wtf.extend(wtfClassify)


const lang =  'en'; // 'af';  // 
const dumpdate = 20240220;
const working_dir = '/Users/mcmenamin/wiki/'
const path_to_file = `${working_dir}/wikidump/${lang}wiki-${dumpdate}-pages-articles.xml`
//const path_to_file = `${working_dir}/wikidump/test.xml`


function parseLinks(doc) {

  const badSectionNames = [
      'Notes',
      'References',
      'External links',
      'Cited works',
  ]

  const rawText = (
      doc.sections()
      .filter(s => !badSectionNames.includes(s.name))
      .map(l => l.wikitext())
      .filter(text => text.trim() !== "")
      .join("\n")
  )

  var output = {
    'title': Buffer.from(doc.title(), 'utf-8').toString(),
    'pageID': doc.pageID(),
    'is_disambig': doc.isDisambiguation(),
    'page_typeroot': doc.classify()['root'],
    'page_type': doc.classify()['type'],
    'raw_text': rawText,
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
  return output

}


process.chdir(working_dir);

dumpster({
  file: path_to_file,
  db: `${lang}wiki`,
  skip_redirects: false,
  skip_disambig: true,
  //workers: 1,
  batch_size: 50,
  custom: parseLinks
});

