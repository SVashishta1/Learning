# Your first VECTOR DATABASE (Chroma). It does project 22's work for you, saves to disk, and adds filters.
import chromadb

db = chromadb.PersistentClient(path="chroma_data")             # saved in the chroma_data folder
recipes = db.get_or_create_collection("recipes", configuration={"hnsw": {"space": "cosine"}})   # a collection = like a table; "cosine" = compare meaning

# ADD documents. Chroma turns each one into numbers (embeddings) automatically.
# "metadatas" are extra labels you can FILTER on, just like columns in a normal database.
recipes.upsert(
    ids=["r1", "r2", "r3", "r4", "r5", "r6"],
    documents=[
        "Spaghetti carbonara with eggs, pecorino cheese and crispy pancetta",
        "Vegan chickpea curry with coconut milk and spinach",
        "Chocolate lava cake with a gooey molten centre",
        "Grilled salmon with lemon, garlic and fresh herbs",
        "Mango smoothie with yogurt and honey",
        "Spicy black bean tacos with avocado and lime",
    ],
    metadatas=[
        {"diet": "meat", "minutes": 25}, {"diet": "vegan", "minutes": 35}, {"diet": "vegetarian", "minutes": 30},
        {"diet": "fish", "minutes": 20}, {"diet": "vegetarian", "minutes": 5}, {"diet": "vegan", "minutes": 15},
    ],
)
print(f"The database holds {recipes.count()} recipes.\n")


def show(title, results):
    print(title)
    for doc, meta, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
        print(f"   {1 - distance:.2f}  {doc}  {meta}")      # Chroma gives "distance": lower = closer
    print()


# SEARCH by meaning
show("🔎 'something sweet for dessert'", recipes.query(query_texts=["something sweet for dessert"], n_results=2))
# SEARCH by meaning + FILTER by label
show("🔎 'a warm dinner' but only vegan", recipes.query(query_texts=["a warm dinner"], n_results=2, where={"diet": "vegan"}))
show("🔎 'healthy food' ready in under 20 minutes",
     recipes.query(query_texts=["healthy food"], n_results=2, where={"minutes": {"$lt": 20}}))

# UPDATE and DELETE work like a normal database
recipes.update(ids=["r5"], documents=["Mango and passion fruit smoothie with oat milk"], metadatas=[{"diet": "vegan", "minutes": 5}])
recipes.delete(ids=["r3"])
print(f"After one update and one delete: {recipes.count()} recipes. Run me again: the data is still saved on disk.")
