
$( document ).ready(function() {

    var outputElement = document.getElementById( "output-vals" );

    function readTopicForm() {
        var formData = $( ".form-control" ).
            val().
            split(";").
            map( x => x.trim().replace(" ", "_") )
        return formData;
    }

    function writeWikiPaths() {

        var groupby = $( ".dropdown-menu" ).
            find( ".dropdown-item.active" ).
            attr('value')

        var output = ""
        if (groupby == "groupby-topic") {
            output = fmtNestedLists(pathsByTopic);
        } else {
            output = fmtNestedLists(pathsByNearby);
        }
        return output;
    }

    function queryWikiPaths(position, topics) {

        const locationAndInterests = JSON.stringify({ 
            "latitude": position.coords.latitude, 
            "longitude": position.coords.longitude,
            "topics": topics
        });

        $.ajax({
            url: "/",
            type: "POST",
            data: locationAndInterests,
            contentType: "application/json",
            dataType: "json",
            success: function (queryResponse) {
                pathsByTopic = queryResponse["nested_lists_by_topic"]
                pathsByNearby = queryResponse["nested_lists_by_nearby"]
                outputElement.innerHTML = writeWikiPaths()
            }
        });        
    }

    $( ".form-control" ).val(
        formatSampleOfTopics(NUM_INIT_TOPICS)
    );

    $( ".dropdown-menu" ).find( ".dropdown-item" ).on(
        "click",
        function() {
            $(this).
                parent( ".dropdown-menu" ).
                find( ".dropdown-item.active" ).
                removeClass( "active" );

            $(this).addClass( "active" );

            outputElement.innerHTML = writeWikiPaths()
        }

    );

    $( ".search-button" ).on(
        'click',
        function() {
            navigator.geolocation.getCurrentPosition(
                pos => queryWikiPaths(pos, readTopicForm()),
                posErr => console.log('geolookup failed!')
            );
            writeWikiPaths();
        }
    );

});
