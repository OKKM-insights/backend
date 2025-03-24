"""
This script updates the ImageClassMeasure (ICM) table schema.
The ICM table is specifically designed for pixel-wise user label aggregation,
storing likelihoods, confidence scores, and helper values for each pixel.
"""

from services.ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector

def main():
    try:
        print("Updating ImageClassMeasure (ICM) schema for pixel-wise user label aggregation...")
        
        # Initialize the database connector
        db = MYSQLImageClassMeasureDatabaseConnector()
        
        # Update the ICM schema
        db.update_schema()
        print("\nICM schema update completed successfully.")
        print("The ICM table is now configured to store:")
        print("- Pixel-wise likelihoods (LONGTEXT)")
        print("- Pixel-wise confidence scores (LONGTEXT)")
        print("- Pixel-wise helper values (LONGTEXT)")
        print("- Image dimensions (width, height)")
        
    except Exception as e:
        print(f"Error during ICM schema update: {str(e)}")
        print("Note: This error only affects the pixel-wise user label aggregation.")
        print("Other functionality (ML detection, Labels, etc.) should still work.")

if __name__ == "__main__":
    main() 