import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os

load_dotenv()

connection_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=3,
    pool_reset_session=True,
    host=os.getenv("DB_HOSTNAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME")
)

def update_schema(connection):
    """Update the database schema if needed."""
    try:
        cursor = connection.cursor()
        
        # Drop tables in order of dependencies
        cursor.execute("DROP TABLE IF EXISTS Labels")
        cursor.execute("DROP TABLE IF EXISTS ImageClassMeasure")
        cursor.execute("DROP TABLE IF EXISTS OriginalImages")
        
        # Create OriginalImages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS OriginalImages (
                ImageID VARCHAR(255) PRIMARY KEY,
                ProjectID INT,
                image LONGBLOB,
                FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID)
            )
        """)
        
        # Create Labels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Labels (
                LabelID INT AUTO_INCREMENT PRIMARY KEY,
                ImageID VARCHAR(255),
                X1 FLOAT,
                Y1 FLOAT,
                X2 FLOAT,
                Y2 FLOAT,
                Confidence FLOAT,
                FOREIGN KEY (ImageID) REFERENCES OriginalImages(ImageID)
            )
        """)
        
        # Create ImageClassMeasure table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ImageClassMeasure (
                MeasureID INT AUTO_INCREMENT PRIMARY KEY,
                ImageID VARCHAR(255),
                ClassName VARCHAR(255),
                Confidence FLOAT,
                FOREIGN KEY (ImageID) REFERENCES OriginalImages(ImageID)
            )
        """)
        
        connection.commit()
        print("Schema updated successfully")
        
    except Exception as e:
        print(f"Error updating schema: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        raise
    finally:
        cursor.close()

def get_db_connection():
    try:
        conn = connection_pool.get_connection()
        update_schema(conn)  # Update schema when getting a new connection
        return conn
    except mysql.connector.errors.PoolError as e:
        raise RuntimeError("Database connection pool exhausted") from e