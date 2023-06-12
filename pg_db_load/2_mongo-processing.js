// run this as mongosh < ./2_mongo-processing.js

use enwiki

// Create title_pageid
db.title_pageid.drop()
db.pages.aggregate([
    {$project: {"title": 1, "page_id": {$toInt: "$pageID"}, "hasPlaceCategory": "$has_place_category"}},
    {$out: "title_pageid"}
])

db.title_pageid.createIndex({"title": 1}, {unique: true})
db.title_pageid.createIndex({"page_id": 1}, {unique: true})
db.title_pageid.estimatedDocumentCount()

// Create links
db.links.drop()
db.in_links.drop()
db.out_links.drop()

db.pages.aggregate([
    {$project: {"page_id": {$toInt: "$pageID"}, "outlinks": 1}},
    {$unwind: {"path": "$outlinks"}},
    {$lookup: {
        "from": "title_pageid",
        "localField": "outlinks",
        "foreignField": "title", 
        "as": "joinedOutput"
    }},
    {$project: {"from_page_id": "$page_id", "to_page_id": "$joinedOutput.page_id"}},
    {$unwind: {"path": "$to_page_id"}},
    {$project: {"_id": {$concat: [{$toString: "$from_page_id"}, "-", {$toString: "$to_page_id"}]}, "from_page_id": 1, "to_page_id": 1}},
    {$out: "links"}
])
db.links.estimatedDocumentCount()


// Create out_links
db.links.aggregate([
    {$group: {"_id": "$from_page_id", "out_links": {$addToSet: "$to_page_id"}}},
    {$out: "out_links"}
])
db.out_links.estimatedDocumentCount()


// Create in_links
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
        "has_place_category": "$hasPlaceCategory",
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
        "has_place_category": 1,
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
