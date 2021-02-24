from mondigy.database import get_database
import prodigy
import json


@prodigy.recipe("mongo-loader", config=("Path to configuration file for loader.", "positional", None, str))
def mongo_loader(config: str):
    """
    Data loader for passing results from a query to a MongoDB collection to a Prodigy recipe.

    Args:
        config: path to db configuration file. See examples/example_loader_config.json

    """

    with open(config) as f:
        config_data = json.load(f)

    db = get_database(config_data)
    source_collection = db[config_data["collection"]]
    query = json.loads(config_data.get("query", "{}"))

    documents = source_collection.find(query)
    if "limit" in config_data and config_data["limit"]:
        documents = documents.limit(config_data["limit"])
    if "sort" in config_data and config_data["sort"]:
        documents = documents.sort(config_data["sort"])

    for doc in documents:
        task = {"text": doc[config_data["text_field"]]}
        for field in config_data["other_fields"].split(","):
            field = field.strip()
            task[field] = doc[field]
        print(json.dumps(task))
