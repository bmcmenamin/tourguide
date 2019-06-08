# tourguide


Whenever I come across a [historical markers](https://www.hmdb.org/) out in the world, I usually read it.




This repo contains an app that can be easily deployed using ghte Google App Engine to search 



First, it uses the geolocaiton built in to many Wikipedia pages to find things that are near your current locations.
Then, it looks at a list of pages for things that you're interested in.
Finally, it looks for the pages that can link things in the first group to things in the second group.

For example:
If I was sitting in [Prospect Park, Brooklyn](https://en.wikipedia.org/wiki/Prospect_Park_(Brooklyn)) and entered in that I was interested in [Star Trek: The Original Series](https://en.wikipedia.org/wiki/Star_Trek:_The_Original_Series), the search results would tell me that:

* The special effects for Start Trek were created by [Linwood G. Dunn](https://en.wikipedia.org/wiki/Linwood_G._Dunn) that attended the nearby [high school](John Jay Educational Campus (Brooklyn)
)
* [Patrick Stewart](https://en.wikipedia.org/wiki/Patrick_Stewart) lives in nearby [Park Slope](https://en.wikipedia.org/wiki/Park_Slope)
* [Isaac Asimov](https://en.wikipedia.org/wiki/Isaac_Asimov) grew up in nearby [Windsor Terrace](https://en.wikipedia.org/wiki/Windsor_Terrace,_Brooklyn)

