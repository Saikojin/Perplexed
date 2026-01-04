import asyncio
import csv
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Configuration (matching default backend settings)
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'roddle')
OUTPUT_DIR = "mongo_export"

async def export_collection(db, collection_name):
    """Export a single collection to a CSV file."""
    print(f"Exporting collection: {collection_name}...")
    
    cursor = db[collection_name].find({})
    documents = await cursor.to_list(length=None)
    
    if not documents:
        print(f"  Collection {collection_name} is empty.")
        return

    # Flatten documents for CSV safety (basic flattening)
    # Note: Nested objects will be stringified
    flattened_docs = []
    all_keys = set()
    
    for doc in documents:
        flat_doc = {}
        for k, v in doc.items():
            if k == '_id':
                flat_doc[k] = str(v)
            elif isinstance(v, (dict, list)):
                flat_doc[k] = str(v)
            else:
                flat_doc[k] = v
            all_keys.add(k)
        flattened_docs.append(flat_doc)
        
    keys = sorted(list(all_keys)) # Sort ensure consistent order
    
    # Ensure output directory exists relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(output_path, exist_ok=True)
    
    filename = os.path.join(output_path, f"{collection_name}.csv")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(flattened_docs)
        
    print(f"  Saved {len(documents)} records to {filename}")

async def main():
    print(f"Connecting to MongoDB at {MONGO_URL}...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Get list of all collections
        collections = await db.list_collection_names()
        print(f"Found {len(collections)} collections: {', '.join(collections)}")
        
        # timestamp the export
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Starting export at {timestamp}...")
        
        for col_name in collections:
            await export_collection(db, col_name)
            
        print("\nExport completed successfully.")
        
    except Exception as e:
        print(f"Error during export: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    # Ensure asyncio loop runs
    asyncio.run(main())
