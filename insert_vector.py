import os

from dotenv import load_dotenv
from pymilvus import MilvusClient

load_dotenv()

client = MilvusClient(
    uri=os.getenv("MILVUS_URI"),
    token=os.getenv("MILVUS_TOKEN")
)

collection_name = "reward_knowledge"

# Check whether test record already exists
existing = client.query(
    collection_name=collection_name,
    filter='reward_id == "SYN-TEST-001"',
    output_fields=["reward_id"]
)

if existing:
    print("Sample record already exists!")
else:
    # Temporary test vector: 384 dimensions
    sample_vector = [0.01] * 384

    data = [
        {
            "vector": sample_vector,
            "reward_id": "SYN-TEST-001",
            "description": "Sample discount voucher reward"
        }
    ]

    result = client.insert(
        collection_name=collection_name,
        data=data
    )

    print("Sample vector inserted successfully!")
    print("Insert result:", result)

client.close()