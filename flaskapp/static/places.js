const WIKI_URL =  "https://en.wikipedia.org/wiki/"
const NUM_INIT_TOPICS = 4


var paths_by_topic = []
var paths_by_nearby = []

function wikititle_to_html(title) {
    url = WIKI_URL + title.split(" ").join("_")
    return "<a href=" + url + ">" + title.split("_").join(" ") + "<a>";
}


function fmt_nested_lists(input) {

    var out_string = ""

    if (Array.isArray(input)) {
        out_string = "<div>"
          + "<ul class=\"list-group border-0 \">"
          + input.map(fmt_nested_lists).join("\n")
          + "</ul>"
        + "</div>";                        
    }
    else {
        out_string = "<li class=\"list-group-item border-0\">"
        + wikititle_to_html(input)
        + "</il>";
    }

    return out_string;
}


function getWikiLinks() {

    var groupby = $( ".dropdown-menu" ).
        find( ".dropdown-item.active" ).
        attr('value')

    var output = ""

    if (groupby == "groupby-topic") {
        output = fmt_nested_lists(paths_by_topic);
    }
    else {
        output = fmt_nested_lists(paths_by_nearby);
    }

    return output;
}


$( document ).ready(function() {

    var outputEl = document.getElementById( "output-vals" );

    $( ".form-control" ).val(
        sample_n_random_topics(NUM_INIT_TOPICS).
        join(", ").
        trim()
    );

    $( ".dropdown-menu" ).
        find( ".dropdown-item" ).
        on(
            "click",
            function(){
                $(this).
                    parent( ".dropdown-menu" ).
                    find( ".dropdown-item.active" ).
                    removeClass( "active" );

                $(this).addClass( "active" );
                outputEl.innerHTML = getWikiLinks()
            }
    );

    $( ".search-button" ).on(
        'click',
        function() {
            var topics = getInterestingTopics();
            getLocation(topics);
        }
    );

    function getInterestingTopics() {
        const topicList = $( ".form-control" ).
            val().
            split(",").
            map( x => x.trim().replace(" ", "_") )

        return topicList;
    }


    function getLocation(topics) {
        outputEl.innerHTML = "Figuring out where you are ...";

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                x => findConnections(topics, x)
            );
        } else { 
            outputEl.innerHTML = "Geolocation is not supported by this browser.";
        }
    }


    function findConnections(interestingTopics, position) {

        const locationAndInterests = { 
            "latitude": position.coords.latitude, 
            "longitude": position.coords.longitude,
            "topics": interestingTopics
        };

        $.ajax({
            url: "/",
            type: "POST",
            data: JSON.stringify(locationAndInterests),
            contentType: "application/json",
            dataType: "json",
            success: function (response) {
                paths_by_topic = response["nested_lists_by_topic"]
                paths_by_nearby = response["nested_lists_by_nearby"]
                outputEl.innerHTML = getWikiLinks()
            }
        });

    }

});
