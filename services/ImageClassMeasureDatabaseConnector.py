from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from .DataTypes import ImageClassMeasure, Label
import urllib.parse
import pymysql
import numpy as np


class ImageClassMeasureDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_imageclassmeasure(self, imageclassmeasure:ImageClassMeasure):
        pass

    @abstractmethod
    def get_imageclassmeasures(self, query:str) -> list[ImageClassMeasure]:
        pass

class NoneDB(ImageClassMeasureDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_imageclassmeasure(self, imageclassmeasure:ImageClassMeasure):
        pass


    def get_imageclassmeasures(self, query:str) -> list[ImageClassMeasure]:
        pass

class MYSQLImageClassMeasureDatabaseConnector(ImageClassMeasureDatabaseConnector):

    def __init__(self, table:str='ImageClassMeasure'):
        self.cnx = None
        self.make_db_connection()
        self.table=table

    def make_db_connection(self):
        """Create a database connection."""
        load_dotenv()
        
        # Get database credentials from environment variables
        user = os.getenv('DB_USER', 'Kartik')
        password = os.getenv('DB_PASSWORD', 'password')
        host = os.getenv('DB_HOSTNAME', 'localhost')
        database = os.getenv('DB_NAME', 'my_image_db')
        
        try:
            # Create the connection URL with proper encoding
            connection_url = f"mysql+pymysql://{user}:{urllib.parse.quote_plus(password)}@{host}/{database}"
            self.cnx = create_engine(connection_url)
            
            # Test the connection
            with self.cnx.connect() as connection:
                print('Database connection successful')
                
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            raise

    def update_schema(self):
        """Update the database schema for ImageClassMeasure table."""
        try:
            with self.cnx.connect() as connection:
                # Read the SQL file
                with open('backend/sql/update_icm_schema.sql', 'r') as file:
                    sql_commands = file.read()
                
                # Execute the SQL commands
                for command in sql_commands.split(';'):
                    if command.strip():
                        connection.execute(text(command))
                connection.commit()
                print("Successfully updated ImageClassMeasure schema")
        except Exception as e:
            print(f"Error updating schema: {str(e)}")
            raise

    def push_imageclassmeasure(self, icm: ImageClassMeasure):
        """Push an ImageClassMeasure to the database."""
        try:
            with self.cnx.connect() as connection:
                # Convert numpy arrays to JSON strings
                likelihoods_json = json.dumps(icm.likelihoods.tolist() if isinstance(icm.likelihoods, np.ndarray) else icm.likelihoods)
                confidence_json = json.dumps(icm.confidence.tolist() if isinstance(icm.confidence, np.ndarray) else icm.confidence)
                helper_values_json = json.dumps(icm.helper_values.tolist() if isinstance(icm.helper_values, np.ndarray) else icm.helper_values)
                
                # Ensure ImageID is a string
                image_id = str(icm.imageID)
                
                # Check if ICM already exists
                result = connection.execute(
                    text("""
                        SELECT COUNT(*) FROM ImageClassMeasure 
                        WHERE ImageID = :image_id AND Label = :label
                    """),
                    {"image_id": image_id, "label": icm.label}
                )
                exists = result.scalar() > 0
                
                if exists:
                    # Update existing ICM
                    connection.execute(
                        text("""
                            UPDATE ImageClassMeasure 
                            SET likelihoods = :likelihoods,
                                confidence = :confidence,
                                helper_values = :helper_values
                            WHERE ImageID = :image_id AND Label = :label
                        """),
                        {
                            "likelihoods": likelihoods_json,
                            "confidence": confidence_json,
                            "helper_values": helper_values_json,
                            "image_id": image_id,
                            "label": icm.label
                        }
                    )
                else:
                    # Insert new ICM
                    connection.execute(
                        text("""
                            INSERT INTO ImageClassMeasure 
                            (ImageID, Label, likelihoods, confidence, helper_values, im_width, im_height)
                            VALUES 
                            (:image_id, :label, :likelihoods, :confidence, :helper_values, :width, :height)
                        """),
                        {
                            "image_id": image_id,
                            "label": icm.label,
                            "likelihoods": likelihoods_json,
                            "confidence": confidence_json,
                            "helper_values": helper_values_json,
                            "width": icm.im_width,
                            "height": icm.im_height
                        }
                    )
                connection.commit()
                print(f"Successfully saved ICM for image {image_id}")
        except Exception as e:
            print(f"Error saving ICM: {str(e)}")
            print("Traceback:")
            import traceback
            traceback.print_exc()
            raise

    def get_imageclassmeasures(self, query:str) -> ImageClassMeasure:
        """Get ImageClassMeasure from database."""
        try:
            with self.cnx.connect() as connection:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results")
                
                if result.rowcount == 0:
                    return None
                    
                # Get the first (and should be only) result
                row = result.fetchone()
                
                # Parse JSON strings back to lists
                likelihoods = np.array(json.loads(row.likelihoods))
                confidence = np.array(json.loads(row.confidence))
                helper_values = np.array(json.loads(row.helper_values))
                
                # Create and return ImageClassMeasure object
                icm = ImageClassMeasure(
                    str(row.ImageID),
                    likelihoods,
                    confidence,
                    helper_values,
                    row.Label,
                    row.im_width,
                    row.im_height
                )
                return icm
                
        except Exception as e:
            print(f"Error getting ICM from database: {str(e)}")
            return None

    def push_icm(self, icm_data):
        """Push an image class measure entry to the database."""
        try:
            connection = self.cnx.connect()
            
            # Insert into ImageClassMeasure table
            command = """
            INSERT INTO ImageClassMeasure (ImageID, ClassName, Confidence)
            VALUES (:image_id, :class_name, :confidence)
            """
            
            result = connection.execute(
                text(command),
                {
                    "image_id": icm_data["ImageID"],
                    "class_name": icm_data["ClassName"],
                    "confidence": icm_data["Confidence"]
                }
            )
            
            connection.commit()
            print(f"Successfully added ICM data for image {icm_data['ImageID']}")
            return result.lastrowid
            
        except Exception as e:
            print(f"Error adding ICM data: {e}")
            return None
        finally:
            connection.close()
            
            
    
      

    
# LD = MYSQLImageClassMeasureDatabaseConnector()       

# l = Label('08500f1e-9eff-4d1a-8d9c-1f1d0a2a2bd6','t','t','class',0,0,0,0,0,0,'0')

# I = ImageClassMeasure('test', None, None, None, 'label', 400, 400)

# LD.push_imageclassmeasure(I)
# res = LD.get_imageclassmeasures("SELECT * FROM ImageClassMeasure Where ImageID = 'test2' and Label = 'label';")
# print(res.likelihoods)