const MAX_INIT_TOPICS = 8
const MAX_TOPICS_CHARS = 160

const DEFAULT_TOPICS = [
    "Abbie Hoffman",
    "Abraham Lincoln",
    "Alternative rock",
    "American Civil War",
    "American Revolution",
    "American Revolutionary War",
    "Bebop",
    "Black Panther Party",
    "Blues",
    "Cesar Chavez",
    "Conspiracy theory",
    "Cryptozoology",
    "Dixieland",
    "Eldridge Cleaver",
    "Fearsome critters",
    "Hoax",
    "Huey Long",
    "Indie rock",
    "Industrial Workers of the World",
    "Jazz",
    "Jerry Rubin",
    "John Brown (abolitionist)",
    "Lewis and Clark Expedition",
    "List of conflicts in North America",
    "List of cryptids",
    "List of incidents of civil unrest in Colonial North America",
    "List of incidents of civil unrest in the United States",
    "Louis Brandeis",
    "Malcolm X",
    "Martin Luther King Jr.",
    "Mathematician",
    "National Academy of Engineering",
    "National Academy of Science",
    "Natural history",
    "Philip Berrigan",
    "Poor People's Campaign",
    "Progressive Party (United States, 1924–34)",
    "Psychedelic rock",
    "Ragtime",
    "Rebellion",
    "Richard Nixon",
    "Rock and Roll Hall of Fame",
    "Samuel Gompers",
    "Scientist",
    "Sea monster",
    "Socialist Party of America",
    "Stokely Carmichael",
    "Students for a Democratic Society",
    "Tammany Hall",
    "Theodore Roosevelt",
    "Unidentified flying object",
    "Weather Underground",
    "Youth International Party"
]

function formatSampleOfTopics(maxTopics, maxChars) {

    var topics = DEFAULT_TOPICS.
        sort( () => 0.5 - Math.random() ).
        slice(1, maxTopics + 1)

    var outString = topics.join("; ")

    if (outString.length > maxChars) {
        outString = outString.
            slice(0, maxChars).split("; ").
            slice(0, -1).join("; ")
    }

    return outString;
}
