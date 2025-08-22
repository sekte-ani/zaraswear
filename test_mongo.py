from pymongo import MongoClient

try:
    client = MongoClient("mongodb+srv://zaraswear08:zaraswear2024@cluster0.4u1zfms.mongodb.net/dbzaraswear?retryWrites=true&w=majority")
    db = client['dbzaraswear']
    print("Connected to MongoDB!")
    print("Databases:", client.list_database_names())
except Exception as e:
    print("Error connecting to MongoDB:", e)
