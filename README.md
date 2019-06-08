# tourguide

This repo contains was inspired by my love of reading [historical markers](https://www.hmdb.org/) and the power of Wikipedia graph traversals like [Six-degrees of Wikipedia](https://github.com/jwngr/sdow).

Using existing APIs maintained by Wikipedia, this app finds pages that connect your current location to whatever you're interested in. It is configured to be easily deployed via Google App Engine so you can spin up your own instance that will run on-demand.


For example:
Let's say that you're walking through [Prospect Park, Brooklyn](https://en.wikipedia.org/wiki/Prospect_Park_(Brooklyn)) and you're really in to [_Star Trek_](https://en.wikipedia.org/wiki/Star_Trek:_The_Original_Series). This app will compare your current location to geo-coordinates on Wikipedia and figure out how those pages connect to the things you're interested in (i.e., _Star Trek_). Combining the geo-location with the Wikipedia graph search will surface fun facts that would normally take a lot of digging to surface. Such as:

* The special effects for Star Trek were created by [Linwood G. Dunn](https://en.wikipedia.org/wiki/Linwood_G._Dunn) that attended a nearby [high school](John_Jay_Educational_Campus_(Brooklyn))
* [Patrick Stewart](https://en.wikipedia.org/wiki/Patrick_Stewart) lives in nearby [Park Slope](https://en.wikipedia.org/wiki/Park_Slope)
* [Isaac Asimov](https://en.wikipedia.org/wiki/Isaac_Asimov) grew up in nearby [Windsor Terrace](https://en.wikipedia.org/wiki/Windsor_Terrace,_Brooklyn)
