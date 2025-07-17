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
    "Conspiracy theory",
    "Cryptozoology",
    "Dixieland",
    "Fearsome critters",
    "Hoax",
    "Indie rock",
    "Jazz",
    "John Brown (abolitionist)",
    "Lewis and Clark Expedition",
    "List of conflicts in North America",
    "List of cryptids",
    "List of incidents of civil unrest in Colonial North America",
    "List of incidents of civil unrest in the United States",
    "Mathematician",
    "National Academy of Engineering",
    "National Academy of Science",
    "Natural history",
    "Psychedelic rock",
    "Ragtime",
    "Richard Nixon",
    "Rock and Roll Hall of Fame",
    "Sea monster",
    "Stokely Carmichael",
    "Students for a Democratic Society",
    "Theodore Roosevelt",
    "Unidentified flying object",
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
