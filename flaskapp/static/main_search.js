var locationAndInterests = { 
    "latitude": null, 
    "longitude": null,
    "topics": [],
    "request_id": null
};

var ajaxCurrentSearch;
var ajaxMonitor;

function create_UUID(){
    var dt = new Date().getTime();
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (dt + Math.random()*16)%16 | 0;
        dt = Math.floor(dt/16);
        return (c=='x' ? r :(r&0x3|0x8)).toString(16);
    });
    return uuid;
}


$( document ).ready(function() {

    var outputElement = document.getElementById( "output-vals" );

    function readTopicForm() {
        var formData = $( ".form-control" ).
            val().
            split(";").
            map( x => x.trim().replace(" ", "_") ).
            filter( x => x.length > 1)
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

    function queryWikiPaths(position, topics) {

        locationAndInterests = { 
            "latitude": position.coords.latitude, 
            "longitude": position.coords.longitude,
            "topics": topics,
            "request_id": create_UUID()
        };

        ajaxCurrentSearch = $.ajax({
            url: "/runQuery",
            type: "POST",
            data: JSON.stringify(locationAndInterests),
            contentType: "application/json",
            dataType: "json",
            success: function (queryResponse) {
                pathsByTopic = queryResponse["nested_lists_by_topic"]
                pathsByNearby = queryResponse["nested_lists_by_nearby"]
                seedsByTopic = queryResponse["topic_seeds"]
                seedsByNearby = queryResponse["nearby_seeds"]
                path_status = queryResponse["path_status"]
                outputElement.innerHTML = generateMainOutput()
            },
            error: function (queryResponse) {
                pathsByTopic = []
                pathsByNearby = []
                seedsByTopic = []
                seedsByNearby = []
                path_status = "error"
                outputElement.innerHTML = generateMainOutput()
            }
        });        
    }

    function monitorQueryStatus(timeoutMS=500) {
        setTimeout(
            function() {
                ajaxMonitor = $.ajax({
                    url: "/queryStatus",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify(locationAndInterests),
                    success: function(data) {
                        if (path_status == "searching") {
                            outputElement.innerHTML = fmtSearchProgress(data["query_status"])
                            monitorQueryStatus();
                        }
                    },
                    dataType: "json"
                });
            },
        timeoutMS);
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
            try { ajaxCurrentSearch.abort(); } catch {}
            try { ajaxMonitor.abort(); } catch {}
            path_status = "searching";
            outputElement.innerHTML = generateMainOutput()

            monitorQueryStatus();
            navigator.geolocation.getCurrentPosition(
                pos => queryWikiPaths(pos, readTopicForm()),
                posErr => function() {path_status = "error";}
            );
            outputElement.innerHTML = generateMainOutput();
        }
    );

});
