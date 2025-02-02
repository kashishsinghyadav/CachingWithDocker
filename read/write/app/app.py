from fastapi import FastAPI, HTTPException
from app.database import create_db_connection
from app.redis_cache import cache

app = FastAPI()

# Read-Through Caching (Fetch from Redis or DB)
def get_item_from_db(item_id):
    cached_item = cache.get(f"item:{item_id}")
    if cached_item:
        return eval(cached_item)  

    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        connection.close()

        if item:
            cache.set(f"item:{item_id}", str(item), ex=300)  # Store in Redis for 5 minutes
        return item
    return None

# Write-Through Caching (Write to DB and Update Redis)
def update_item_in_db(item_id, new_data):
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE products SET name = %s, price = %s WHERE id = %s",
            (new_data["name"], new_data["price"], item_id)
        )
        connection.commit()
        connection.close()

        cache.set(f"item:{item_id}", str(new_data), ex=300)  # Update Redis cache
        return True
    return False

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = get_item_from_db(item_id)
    if item:
        return {"item": item}
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: dict):
    success = update_item_in_db(item_id, item)
    if success:
        return {"message": "Item updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update item")

@app.get("/items")
async def get_all_items():
    connection = create_db_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        items = cursor.fetchall()
        connection.close()
        return {"items": items}
    raise HTTPException(status_code=500, detail="Failed to fetch items")
