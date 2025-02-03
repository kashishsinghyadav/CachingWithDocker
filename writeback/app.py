from fastapi import FastAPI
import redis
import pymysql
import json
import time
import threading

app = FastAPI()

# Redis Connection
redis_client = redis.StrictRedis(host="redis_container1", port=6379, db=0, decode_responses=True)

# MySQL Connection
db_connection = pymysql.connect(
    host="mysql_container1",
    user="user",
    password="root",
    database="test_db",
    cursorclass=pymysql.cursors.DictCursor,
    auth_plugin='mysql_native_password'

)

# Background thread to sync cache with database periodically
def sync_cache_to_db():
    while True:
        time.sleep(10)  # Sync every 10 seconds
        keys = redis_client.keys("product:*")  # Fetch all product keys
        if keys:
            cursor = db_connection.cursor()
            for key in keys:
                product_id = key.split(":")[-1]
                product_data = json.loads(redis_client.get(key))
                
                # Update the database
                sql = """INSERT INTO products (id, name, price) 
                         VALUES (%s, %s, %s) 
                         ON DUPLICATE KEY UPDATE name=%s, price=%s"""
                cursor.execute(sql, (product_id, product_data["name"], product_data["price"], 
                                     product_data["name"], product_data["price"]))
                db_connection.commit()
                
                # Remove from cache after writing to DB
                redis_client.delete(key)
            cursor.close()

# Run background sync thread
threading.Thread(target=sync_cache_to_db, daemon=True).start()


# **Write Operation (Write-Back)**
@app.post("/products/{product_id}")
def write_product(product_id: int, name: str, price: float):
    product_key = f"product:{product_id}"
    product_data = {"name": name, "price": price}
    
    # Write to Redis (Cache First)
    redis_client.set(product_key, json.dumps(product_data))
    
    return {"message": "Product written to cache (DB will update later)", "data": product_data}


# Read Operation (Cache First)**
@app.get("/products/{product_id}")
def read_product(product_id: int):
    product_key = f"product:{product_id}"
    
    # Try fetching from Redis first
    product_data = redis_client.get(product_key)
    
    if product_data:
        return {"source": "cache", "data": json.loads(product_data)}
    
    # If not in Redis, fetch from MySQL
    cursor = db_connection.cursor()
    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    result = cursor.fetchone()
    cursor.close()

    if result:
        redis_client.set(product_key, json.dumps(result))  # Cache it for future reads
        return {"source": "database", "data": result}
    
    return {"message": "Product not found"}


