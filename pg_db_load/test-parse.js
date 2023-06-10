import wtf from 'wtf_wikipedia'


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


let doc = await wtf.fetch('Clean Needle Technique')
//let doc = await wtf.fetch(4151174, {follow_redirects: false})
const output = parseLinks(doc)
console.log(output)
