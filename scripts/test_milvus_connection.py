import os

from dotenv import load_dotenv
from pymilvus import MilvusClient

load_dotenv()

MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")

client = MilvusClient(
    uri=MILVUS_URI,
    token=MILVUS_TOKEN
)

if client.has_collection("connection_test"):
    print("Milvus connection successful!")
else:
    print("Milvus connection successful!")
    print("No test collection exists yet.")

client.close()