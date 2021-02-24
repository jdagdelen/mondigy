## mondigy

Mondigy is a small library for using a Mongodb database as a data loader 
for [Prodigy](https://prodi.gy) annotation applications.

## Motivation
Prodigy naviely supports loading text data from files and dataset objects, 
but annotating data that is stored in a MongoDB database requires a custom
data loader. With *mondigy* you can simply write a small config file with 
your database config and have an easy way to get data from Mongo to Prodigy. 

## Features
* Annotate text data from MongoDB
* Pipe data directly from your MongoDB database to your Prodigy application

## Code Example
Let's define a db connection and start annotating data from our MongoDB database!

*Step 1.* Create a config file. For this example, we'll call it `my_db_config.json`.

##### my_db_config.json
```angular2
{
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
}
```

*Step 2.* Start your Prodigy server and let mondigy point your MongoDB collection at it by 
supplying the paths of your config file and the Mondigy loader.

```prodigy mongo-loader my_db_config.json -F mondigy/loader.py | prodigy ner.manual ner_test en_core_web_sm - --label FEATURE,KEYWORD```


*Step 3.* Annotate! 



## Installation
To install Mondigy, simply clone this repo via `git clone https://github.com/jdagdelen/mondigy.git`.

## License

MIT © [John Dagdelen](jdagdelen.github.io)