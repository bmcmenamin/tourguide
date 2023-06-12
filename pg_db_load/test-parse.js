import wtf from 'wtf_wikipedia';
import plugin from 'wtf-plugin-classify'
const extendedWtf = wtf.extend(plugin);


function parseLinks(doc) {

  const badSectionNames = [
      'Notes',
      'References',
      'External links'
  ]

  var output = {
    'title': Buffer.from(doc.title(), 'utf-8').toString(),
    'pageID': doc.pageID(),
    'page_type': doc.classify()['type']
  }

  const redirectLinks = (
      [doc.redirectTo()]
      .filter(s => s !== null)
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


let doc = await extendedWtf.fetch('Clean Needle Technique')
//let doc = await extendedWtf.fetch('Mike Kappus')
const output = parseLinks(doc)
console.log(output)
