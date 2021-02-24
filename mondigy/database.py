import os
from pymongo import MongoClient


def get_database(config_data):
    """
    Configures a pymongo database connection from a config data directory.
    Alternatively, if no config data is provided, it will use environment variables.

    Args:
        config_data (dict): dictionary containing database config info

    Returns:
        pymongo database connection

    """
    MONGO_HOSTNAME = config_data.get("host", None) or os.environ['MONGO_HOSTNAME']
    MONGO_DB = config_data.get("database", None) or os.environ['MONGO_DB']
    MONGO_USERNAME = config_data.get("user", None) or os.environ['MONGO_USERNAME']
    MONGO_PASSWORD = config_data.get("password", None) or os.environ['MONGO_PASSWORD']
    MONGO_AUTHENTICATION_DB = config_data.get("auth_source", None) or os.environ['MONGO_AUTHENTICATION_DB']


    client = MongoClient(host=MONGO_HOSTNAME,
                         username=MONGO_USERNAME,
                         password=MONGO_PASSWORD,
                         authSource=MONGO_AUTHENTICATION_DB)

    return client[MONGO_DB]
