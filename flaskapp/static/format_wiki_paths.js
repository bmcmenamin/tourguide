const WIKI_URL =  "https://en.wikipedia.org/wiki/"

var pathsByTopic = []
var pathsByNearby = []
var searchComplete = false


function wikititle_to_html(title) {
    url = WIKI_URL + title.split(" ").join("_")
    return "<a href=" + url + " target=\"_blank\">" + title.split("_").join(" ") + "<a>";
}


function fmtNestedLists(input) {
    if (Array.isArray(input)) {
        return "<div>"
          + "<ul class=\"list-group border-0 \">"
          + input.map(fmtNestedLists).join("\n")
          + "</ul>"
        + "</div>";                        
    }
    else {
        return "<li class=\"list-group-item border-0\">"
        + wikititle_to_html(input)
        + "</il>";
    }
}