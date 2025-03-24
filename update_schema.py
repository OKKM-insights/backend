from services.ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector

def main():
    try:
        # Initialize the database connector
        db = MYSQLImageClassMeasureDatabaseConnector()
        
        # Update the schema
        db.update_schema()
        print("Schema update completed successfully")
        
    except Exception as e:
        print(f"Error during schema update: {str(e)}")

if __name__ == "__main__":
    main() 