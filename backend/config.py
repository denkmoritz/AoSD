import os

class Config:
    api_key_openaq = os.getenv("api_key_open_aq", "bd4abee7cfa6bc34df460759e71b2a5834ead20542afd4231f4e642409bb143e")
    api_key_openweather = os.getenv("api_key_openweather", "d936429564d5be4cd5b1e1545b3fe100")