import os

from dotenv import load_dotenv
from pymilvus import MilvusClient

load_dotenv()

client = MilvusClient(
    uri=os.getenv("MILVUS_URI"),
    token=os.getenv("MILVUS_TOKEN")
)

result = client.query(
    collection_name="reward_knowledge",
    filter='reward_id == "SYN-TEST-001"',
    output_fields=[
        "primary_key",
        "reward_id",
        "description"
    ]
)

print("Retrieved records:")
print(result)

client.close()