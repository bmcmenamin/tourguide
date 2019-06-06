const WIKI_URL =  "https://en.wikipedia.org/wiki/"
const NUM_INIT_TOPICS = 4


function wikititle_to_html(title) {
    url = WIKI_URL + title.split(" ").join("_")
    return "<a href=" + url + ">" + title.split("_").join(" ") + "<a>";
}

function fmt_nested_lists(i) {
    var out_string = ""

    if (Array.isArray(i)) {
        out_string = "<div>"
          + "<ul class=\"list-group border-0 \">"
          + i.map(fmt_nested_lists).join("\n")
          + "</ul>"
        + "</div>";                        
    }
    else {
        out_string = "<li class=\"list-group-item border-0\">"
        + wikititle_to_html(i)
        + "</il>";
    }
    return out_string;
}


$( document ).ready(function() {

    var outputEl = document.getElementById( "output-vals" );

    $( ".form-control" ).val(
        sample_n_random_topics(NUM_INIT_TOPICS).
        join(", ").
        trim()
    )
    
    $( ".search-button" ).click(
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
                outputEl.innerHTML = "Checking out what's around here";
                outputEl.innerHTML = fmt_nested_lists(response["nested_lists_by_topic"])
            },

            error: function () {
                outputEl.innerHTML = "An error occured while finding nearby places";
            }
        });
    }

});
