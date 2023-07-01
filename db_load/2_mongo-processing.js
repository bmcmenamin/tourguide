// run this as mongosh < ./2_mongo-processing.js

use enwiki

// Create title_pageid
db.title_pageid.drop()
db.pages.aggregate([
    {$project: {
        "title": 1,
        "titleCapitalized": {$toUpper: "$title"},
        "page_id": {$toInt: "$pageID"},
        "is_disambig": "$is_disambig",
        "page_typeroot": "$page_typeroot",
        "page_type": "$page_type"
    }},
    {$out: "title_pageid"}
])

db.title_pageid.createIndex({"title": 1}, {unique: true})
db.title_pageid.createIndex({"titleCapitalized": 1}, {unique: false})
db.title_pageid.createIndex({"page_id": 1}, {unique: true})
db.title_pageid.estimatedDocumentCount()

// Create links
db.links.drop()
db.pages.aggregate([
    {$project: {
        "page_id": {$toInt: "$pageID"},
        "outlinks": 1
    }},
    {$unwind: {"path": "$outlinks"}},
    {$project: {
        "page_id": 1,
        "outlinks": 1,
        "outlinksCapitalized": {$toUpper: "$outlinks"}
    }},
    {$lookup: {
        "from": "title_pageid",
        "localField": "outlinksCapitalized",
        "foreignField": "titleCapitalized", 
        "as": "joinedOutputCapitalized"
    }},
    {$project: {
        "from_page_id": "$page_id",
        "outlinks": 1,
        "to_page_id": "$joinedOutputCapitalized.page_id"
    }},
    {$unwind: {"path": "$to_page_id"}},
    {$group: {
        "_id": {$concat: [{$toString: "$from_page_id"}, "-", {$toString: "$to_page_id"}]},
        "outlinks": {"$first": "$outlinks"},
        "from_page_id": {"$first": "$from_page_id"},
        "to_page_id": {"$first": "$to_page_id"},
    }},
    {$out: "links"}
])

db.links.createIndex({"from_page_id": 1}, {unique: false})
db.links.createIndex({"to_page_id": 1}, {unique: false})
db.links.estimatedDocumentCount()


// Create out_links
db.out_links.drop()
db.links.aggregate([
    {$group: {"_id": "$from_page_id", "out_links": {$addToSet: "$to_page_id"}}},
    {$out: "out_links"}
])
db.out_links.estimatedDocumentCount()


// Create in_links
db.in_links.drop()
db.links.aggregate([
    {$group: {"_id": "$to_page_id", "in_links": {$addToSet: "$from_page_id"}}},
    {$out: "in_links"}
])
db.in_links.estimatedDocumentCount()


// join into final table
db.page_links.drop()
db.title_pageid.aggregate([
    {$lookup: {
        "from": "out_links",
        "localField": "page_id",
        "foreignField": "_id", 
        "as": "joined_out_links"
    }},
    {$lookup: {
        "from": "in_links",
        "localField": "page_id",
        "foreignField": "_id", 
        "as": "joined_in_links"
    }},
    {$project: {
        "_id": "$page_id",
        "page_id": "$page_id",
        "title": 1,
        "is_disambig": "$is_disambig",
        "page_type": 1,
        "page_typeroot": 1,
        "in_links": {$reduce: {
            input: "$joined_in_links.in_links",
            initialValue: [],
            in: {$concatArrays: ["$$value", "$$this"]}
        }},
        "out_links": {$reduce: {
            input: "$joined_out_links.out_links",
            initialValue: [],
            in: {$concatArrays: ["$$value", "$$this"]}
        }}
    }},
    {$project: {
        "_id": 1,
        "page_id": 1,
        "title": 1,
        "is_disambig": 1,
        "page_type": 1,
        "page_typeroot": 1,
        "in_links": 1,
        "out_links": 1,
        "num_in_links": {$ifNull: [{$size: "$in_links"}, 0]},
        "num_out_links": {$ifNull: [{$size: "$out_links"}, 0]},
    }},
    {$out: "page_links"}
])
db.page_links.estimatedDocumentCount()


// cleanup
db.title_pageid.drop()
db.links.drop()
db.in_links.drop()
db.out_links.drop()
