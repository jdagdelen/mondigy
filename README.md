## mondigy

Mondigy is a small library for using a Mongodb database as a data loader 
for [Prodigy](https://prodi.gy) annotation applications.

## Motivation
Prodigy naviely supports loading text data from files and dataset objects, 
but annotating data that is stored in a MongoDB database is not natively 
supported. 

With *mondigy* you can annotate data from a MongoDB collection 
and store your annotations in a MongoDB database.

## Features
* Annotate text data from MongoDB
* Pipe data directly from your MongoDB database to your Prodigy application


## Installation & Setup

Mondigy can be installed via `pip install mondigy` or by cloning this repo and 
running `python setup.py` in the project root.

Mondigy will set up the collections it requires in your mongo database. They are 
named with a `_p.<collection_name>`convention. Don't delete these collections or 
manually edit any of the documents in them.

To set up mondigy, just enter your MongoDB connection info into your 
[prodigy.json config file](https://prodi.gy/docs/install#config),
which is found in your `PRODIGY_HOME` directory. The source database and annotations 
database (where your completed annotations are stored by Prodigy) can be configured 
independently or the same database can be specified for both if you want everything
in the same db. See [/example_config/prodigy.json](/example_config/prodigy.json)
for an example config file.

## Code Example
Let's define a db connection and start annotating data from our MongoDB database!

*Step 1.* Add configuration parameters to `prodigy.json` in your `PRODIGY_HOME` directory. For this example, 
we'll be limiting our annotations to the 1000 entries that are `in_stock` from the `products` collection 
of our database. We'll also include the product name and product id in the data returned to Prodigy 
so we can include that information in a custom view. .

##### my_db_config.json
```
  ...
  "db": "mondigy.db",
  "db_settings": {
    "mongodb": {
      "source_db": {
        "host": "my.database.com",
        "user": "mongo_user",
        "password": "mongo_pass",
        "database": "my_db",
        "auth_source": "admin",
        "collection": "products",
        "text_field": "description",
        "other_fields": ["product_name", "product_id"],
        "query": {"in_stock": true},
        "limit": 1000
      },
      "annotations_db": {
        "host": "my.database.com",
        "user": "mongo_user",
        "password": "mongo_pass",
        "database": "my_db",
        "auth_source": "admin",
      }
    }
  },
  ...
}
```

*Step 2.* Start your Prodigy server and let mondigy point your MongoDB collection at it by 
supplying the paths of your config file and the Mondigy loader.

```prodigy ner.manual my_ner_task en_core_web_sm - --label FEATURE,KEYWORD```


*Step 3.* Annotate! 

## License

MIT © [John Dagdelen](jdagdelen.github.io)