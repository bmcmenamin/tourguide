const WIKI_URL =  "https://en.wikipedia.org/wiki/"

var pathsByTopic = []
var pathsByNearby = []
var seedsByTopic = []
var seedsByNearby = []
var path_status = 'unknown'

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


function fmtFailedSearchSummary(topics, nearby) {

    var output = "<div>"
        + "<div><p>No pages found that can connect these " +topics.length +" topics:</p>"
        + fmtNestedLists(topics)
        + "<br></div>"
        + "<div><p>... to these " +nearby.length +" nearby places:</p>"
        + fmtNestedLists(nearby)
        + "<br></div>"
        + "</div>"; 
    return output;
}


function fmtSearchProgress(statusUpdates) {

    var output = "<div><ul class=\"list-group border-0 \">"
        + statusUpdates.map(i => "<il>" +i +"</il>").join("\n")
        + "</ul></div>";

    return output;
}
