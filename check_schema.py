from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

def main():
    try:
        # Load environment variables
        load_dotenv('backend/.env')
        
        # Create database connection
        connection_url = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOSTNAME')}/{os.getenv('DB_NAME')}"
        engine = create_engine(connection_url)
        
        # Check OriginalImages table schema
        with engine.connect() as conn:
            result = conn.execute(text('DESCRIBE OriginalImages'))
            print("\nOriginalImages table schema:")
            for row in result:
                print(row)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 