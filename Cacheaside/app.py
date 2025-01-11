
from fastapi import FastAPI, HTTPException
import redis
import mysql.connector
from mysql.connector import Error
from typing import Dict, List

app = FastAPI()

cache = redis.Redis(host="redis", port=6379, decode_responses=True)

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="mysql",  
            user="root",
            password="root",
            database="test_db"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_item_from_db(item_id: int) -> Dict:
    cached_item = cache.get(str(item_id))
    if cached_item:
        return eval(cached_item)  

    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            connection.close()

            if item:
                cache.set(str(item_id), str(item), ex=60)
            return item
        except Error as e:
            print(f"Error fetching item from DB: {e}")
            connection.close()
            return None
    return None

def update_item_in_db(item_id: int, new_data: Dict) -> bool:
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE products SET name = %s, price = %s WHERE id = %s",
                (new_data["name"], new_data["price"], item_id)
            )
            connection.commit()
            connection.close()

            cache.delete(str(item_id))
            return True
        except Error as e:
            print(f"Error updating item in DB: {e}")
            connection.close()
            return False
    return False

def get_all_items_from_db() -> List:
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM products")
            items = cursor.fetchall()
            connection.close()
            return items
        except Error as e:
            print(f"Error fetching items from DB: {e}")
            connection.close()
            raise HTTPException(status_code=500, detail="Failed to fetch items from database")
    else:
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    item = get_item_from_db(item_id)
    if item:
        return {"item": item}
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Dict):
    success = update_item_in_db(item_id, item)
    if success:
        return {"message": "Item updated successfully"}
    raise HTTPException(status_code=500, detail="Failed to update item")

@app.get("/items")
async def get_all_items():
    return {"items": get_all_items_from_db()}

@app.post("/items")
async def create_item(item: Dict):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO products (name, price) VALUES (%s, %s)",
                (item["name"], item["price"])
            )
            connection.commit()
            connection.close()
            return {"message": "Item created successfully"}
        except Error as e:
            print(f"Error creating item in DB: {e}")
            connection.close()
            raise HTTPException(status_code=500, detail="Failed to create item")
    else:
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    connection = create_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM products WHERE id = %s",
                (item_id,)
            )
            connection.commit()
            connection.close()
            cache.delete(str(item_id))
            return {"message": "Item deleted successfully"}
        except Error as e:
            print(f"Error deleting item from DB: {e}")
            connection.close()
            raise HTTPException(status_code=500, detail="Failed to delete item")
    else:
        raise HTTPException(status_code=500, detail="Database connection failed")
