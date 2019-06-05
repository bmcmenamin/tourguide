var WIKI_URL =  "https://en.wikipedia.org/wiki/"


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



    $( ".search-button" ).click(
        function() { getLocation(); }
    );

    function getLocation() {
        outputEl.innerHTML = "Searching...";

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(fetchPlaces);
        } else { 
            outputEl.innerHTML = "Geolocation is not supported by this browser.";
        }
    }

    function fetchPlaces(position) {

        var data = { 
            "latitude": position.coords.latitude, 
            "longitude": position.coords.longitude
        };

        $.ajax({
            url: "/",
            type: "POST",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",

            success: function (response) {
                outputEl.innerHTML = fmt_nested_lists(response["nested_lists_by_topic"])
                add_toggles()

            },

            error: function () {
                outputEl.innerHTML = "An error occured while fetching places";
            }
        });
    }
});
