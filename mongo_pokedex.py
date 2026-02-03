import os
import requests
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import streamlit as st

MONGO_URI = st.secrets["MONGO_URI"]
DB_NAME = st.secrets["DB_NAME"]
COLLECTION_NAME = st.secrets["COLLECTION_NAME"]


client = MongoClient(MONGO_URI)
db = client[DB_NAME]                     
col = db[COLLECTION_NAME]                

def ensure_indexes():
    # índices útiles para búsqueda/ordenación
    col.create_index([("name", ASCENDING)], unique=True)
    col.create_index([("pokemon_id", ASCENDING)], unique=True)
    col.create_index([("types", ASCENDING)])

def fetch_pokemon(pokemon_id: int) -> dict:
    url = f"https://pokeapi.co/api/v2/pokemon/ditto/{pokemon_id}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    p = r.json()

    doc = {
        "pokemon_id": p["id"],
        "name": p["name"],
        "height": p["height"],
        "weight": p["weight"],
        "base_experience": p.get("base_experience"),
        "types": [t["type"]["name"] for t in p["types"]],
        "stats": {s["stat"]["name"]: s["base_stat"] for s in p["stats"]},
        "sprite": p["sprites"]["front_default"],
        "updated_at": None,
    }
    return doc

#  insertar datos
def insert_many_from_pokeapi(start_id: int, end_id: int):
    ensure_indexes()
    inserted, skipped = 0, 0

    for pid in range(start_id, end_id + 1):
        doc = fetch_pokemon(pid)
        # upsert: si existe, lo actualiza; si no, lo inserta
        res = col.update_one(
            {"pokemon_id": doc["pokemon_id"]},
            {"$setOnInsert": doc},
            upsert=True
        )
        if res.upserted_id:
            inserted += 1
        else:
            skipped += 1

    return {"inserted": inserted, "skipped_existing": skipped}

# búsqueda (filtros)
def search_pokemons(
    name_contains: str | None = None,
    pokemon_id: int | None = None,
    type_is: str | None = None,
    min_weight: int | None = None,
    max_weight: int | None = None,
    sort_field: str = "pokemon_id",
    sort_dir: int = 1,  # 1 asc, -1 desc
    limit: int = 10,
    skip: int = 0
):
    query = {}

    if pokemon_id is not None:
        query["pokemon_id"] = pokemon_id

    if name_contains:
        query["name"] = {"$regex": name_contains, "$options": "i"}

    if type_is:
        query["types"] = type_is

    if min_weight is not None or max_weight is not None:
        query["weight"] = {}
        if min_weight is not None:
            query["weight"]["$gte"] = min_weight
        if max_weight is not None:
            query["weight"]["$lte"] = max_weight

    cursor = (
        col.find(query, {"_id": 0})
        .sort(sort_field, ASCENDING if sort_dir == 1 else DESCENDING)
        .skip(skip)
        .limit(limit)
    )

    results = list(cursor)
    total = col.count_documents(query)

    return {"total": total, "results": results, "query": query}

#  update
def update_pokemon(name: str, fields: dict):
    # ejemplo fields: {"weight": 999, "height": 1, "updated_at": "2026-02-03"}
    return col.update_one({"name": name}, {"$set": fields})

#  eliminar datos
def delete_one_by_name(name: str):
    return col.delete_one({"name": name})

def delete_many_by_type(type_name: str):
    return col.delete_many({"types": type_name})

#  eliminar colección
def drop_collection():
    col.drop()
    return True

# (extra) eliminar database completa
def drop_database():
    client.drop_database(DB_NAME)
    return True
