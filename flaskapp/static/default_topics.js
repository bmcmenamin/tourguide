const DEFAULT_TOPICS = [
    "Huey Long",
    "Richard Nixon",
    "Progressive Party (United States, 1924–34)",
    "Socialist Party of America",
    "Industrial Workers of the World",
    "List of incidents of civil unrest in the United States",
    "Indie rock",
    "Psychedelic rock",
    "Alternative rock",
    "Green Bay Packers",
    "Rock and Roll Hall of Fame",
    "Mathematician",
    "Scientist",
    "National Academy of Engineering",
    "National Academy of Science",
    "Natural history",
    "Conspiracy theory",
    "Cryptozoology",
    "Fearsome critters",
    "Sea monster",
    "Hoax",
    "Unidentified flying object",
    "List of cryptids"
]

function sample_n_random_topics(n) {
    var topics = DEFAULT_TOPICS.
        sort( () => 0.5 - Math.random()).
        slice(1, n + 1);
    return topics
}
