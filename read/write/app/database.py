import mysql.connector
from mysql.connector import Error

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host="mysql_container",  # Container name from docker-compose
            user="root",
            password="root",
            database="test_db"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
