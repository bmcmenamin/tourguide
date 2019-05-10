$( document ).ready(function() {
    var x = document.getElementById( "places-list" );
    
    $( ".btn-search" ).click(
        function() { getLocation(); }
    );

    function getLocation() {
        x.innerHTML = "Searching...";

        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(fetchPlaces);
        } else { 
            x.innerHTML = "Geolocation is not supported by this browser.";
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
                var places = response["results"]

                x.innerHTML = "";
                
                for (var p in places) {
                    x.innerHTML +=
                        "<div class=\"item\">" +
                        "<a href=\"" +places[p]["url"] + "\">" +
                        places[p]["title"] +
                        "</div>";
                }
            },

            error: function () {
                x.innerHTML = "An error occured while fetching places";
            }
        });
    }
});
