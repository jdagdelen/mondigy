## Mondigy configuration parameters
The following parameters go in `prodigy.json` in your Prodigy Home

* "host": "Hostname of MongoDB service."
* "user": "Username for MongoDB"
* "password": "Password for MongoDB"
* "database": "Database you want to pull from."
* "auth_source": "Auth Database for MongoDB. If unknown, try the database name."
* "mongo_uri": "Alternatively, you can use a full mongodb URI instead."
* "collection": "Name of collection to load documents from."
* "text_field": "Name of the field that contains the text to be annotated.e.g. 'abstract'"
* "other_fields": "Names of other fields to include for display, separated by commas. e.g. 'title,authors,doi'"
* "query": "Query dictionary to pass to collection's find() method. To get all data, use empty dict (e.g. '{}'). Used to load examples from source collection"
* "sort": "Sort list to pass to collection find() method. e.g. ['date', -1]. Used to load examples from source collection"
* "limit": "Limit for number of documents in task. e.g. 1000. Used to load examples from source collection"