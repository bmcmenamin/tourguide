$( document ).ready(function() {


    var outputElement = document.getElementById( "output-vals" );


    function readTopicForm() {
        var formData = $( ".form-control" ).
            val().
            split(";").
            map( x => x.trim().split(" ").join("_") ).
            filter( x => x.length > 1);
        return formData;
    }


    function generateMainOutput() {

        switch(path_status) {

            case "error":
                return "<div>Something went wrong. ¯\\\_(ツ)_/¯</div>";

            case "no_paths":
                return fmtFailedSearchSummary(seedsByTopic, seedsByNearby);

            case "has_paths":

                var groupby = $( ".dropdown-menu" ).
                    find( ".dropdown-item.active" ).
                    attr('value');

                switch(groupby) {
                    case "groupby-nearby":
                        return fmtNestedLists(pathsByNearby);
                    default:
                        return fmtNestedLists(pathsByTopic);
                }

            default:
                return "";
        }
    }


    function clearSession() {

        return $.ajax({
            url: "/clearSession",
            type: "POST",
            contentType: "application/json",
            dataType: "json",
        })
    }


    function setLocation() {

        var good_func = function(location) {
            $.ajax({
                url: "/setLocation",
                type: "POST",
                data: JSON.stringify(location),
                contentType: "application/json",
                dataType: "json",
                error: function (queryResponse) {
                    path_status = "error"
                    outputElement.innerHTML = generateMainOutput()
                }
            });
        }

        return navigator.geolocation.getCurrentPosition(
            function(pos) {
                good_func({
                    "latitude": pos.coords.latitude, 
                    "longitude": pos.coords.longitude
                })
            }
        );
    }


    function setTopics(topics) {

        return $.ajax({
            url: "/setTopics",
            type: "POST",
            data: JSON.stringify(topics),
            contentType: "application/json",
            dataType: "json",
            error: function (queryResponse) {
                path_status = "error"
                outputElement.innerHTML = generateMainOutput()
            }
        })

    }


    function runQuery() {

        var good_func = function (queryResponse) {
            pathsByTopic = queryResponse["nested_lists_by_topic"]
            pathsByNearby = queryResponse["nested_lists_by_nearby"]
            seedsByTopic = queryResponse["topic_seeds"]
            seedsByNearby = queryResponse["nearby_seeds"]
            path_status = queryResponse["path_status"]
            outputElement.innerHTML = generateMainOutput();
        }

        var bad_func = function (queryResponse) {
            pathsByTopic = []
            pathsByNearby = []
            seedsByTopic = []
            seedsByNearby = []
            path_status = "error"
            outputElement.innerHTML = generateMainOutput();
        }

        return $.ajax({
            url: "/runQuery",
            type: "POST",
            contentType: "application/json",
            dataType: "json",
            success: good_func,
            error: bad_func
        })
    }


    $( ".form-control" ).val(
        formatSampleOfTopics(MAX_INIT_TOPICS, MAX_TOPICS_CHARS)
    );


    $( ".dropdown-menu" ).find( ".dropdown-item" ).on(
        "click",
        function() {
            $(this).
                parent( ".dropdown-menu" ).
                find( ".dropdown-item.active" ).
                removeClass( "active" );

            $(this).addClass( "active" );
            outputElement.innerHTML = generateMainOutput()
        }

    );


    $( ".search-button" ).on(
        'click',
        function() {

            path_status = "searching";

            var promises = clearSession().then(
                setTopics(readTopicForm())
            ).then(
                setLocation()
            ).then(
                runQuery()
            );

        }
    );

});
