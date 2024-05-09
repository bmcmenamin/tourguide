import wtf from 'wtf_wikipedia';
import wtfClassify from 'wtf-plugin-classify';
wtf.extend(wtfClassify)

function parseLinks(doc) {

  const badSectionNames = [
      'Notes',
      'References',
      'External links',
      'Cited Works'
  ]

  const rawText = (
      doc.sections()
      .filter(s => !badSectionNames.includes(s.name))
      .map(l => l.wikitext())
      .join("\n")
  )

  const cleanText = (
      doc.sections()
      .filter(s => !badSectionNames.includes(s.name))
      .map(l => l.text())
      .join("\n")
  )

  var output = {
    'title': Buffer.from(doc.title(), 'utf-8').toString(),
    'pageID': doc.pageID(),
    'is_disambig': doc.isDisambiguation(),
    'page_typeroot': doc.classify()['root'],
    'page_type': doc.classify()['type'],
    'raw_text': rawText,
    'clean_text': cleanText
  }

  const redirectLinks = (
      [doc.redirectTo()]
      .filter(s => s !== null)
      .filter(s => 'page' in s)
      .filter(s => s.page != doc.title())
      .map(s => s.page)
  )

  const allSectionLinks = (
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

  const linksByParagraph = (
      doc.sections()
      .filter(s => !badSectionNames.includes(s.title()))
      .flatMap(s => s.paragraphs().map(p => [s.title(), p.json()]))
      .map(sp => ({
        section: sp[0],
        text: sp[1].sentences
            .flatMap(s=>s.text)
            .join(" "),

        links: sp[1].sentences
            .flatMap(s => s.links)
            .filter(v => v !== undefined)
            .filter(l => l.type == 'internal')
            .map(l => l.page)
      }))
  )

  const linksByInfobox = (
      doc.infoboxes()
      .flatMap(b => Object.entries(b.json()))
      .filter(kv => kv[1].links !== undefined)
      .map(kv => ({
        section: `INFOBOX ${kv[0]}`,
        text: kv[1].text,
        links: kv[1].links
            .filter(l => l.type == 'internal')
            .map(l => l.page)
      }))  )

  const outlinks = [...new Set([...redirectLinks, ...allSectionLinks, ...infoboxLinks])]
  output['outlinks'] = outlinks.map(s => Buffer.from(s, 'utf-8').toString())

  output['linksByParagraph'] = linksByParagraph.concat(linksByInfobox);

  return output
}


//let doc = await wtf.fetch('Clean Needle Technique')
let doc = await wtf.fetch('Roky Erickson')
const output = parseLinks(doc)
console.log(output)
