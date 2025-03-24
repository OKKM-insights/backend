from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from .DataTypes import Label
import urllib.parse
import pymysql
import traceback


class LabelDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_label(self, label:Label):
        pass

    @abstractmethod
    def get_labels(self, query:str) -> list[Label]:
        pass

class NoneDB(LabelDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_label(self, label:Label):
        pass


    def get_labels(self, query:str) -> list[Label]:
        pass

class MYSQLLabelDatabaseConnector(LabelDatabaseConnector):

    def __init__(self, table:str='Labels'):
        self.cnx = None
        self.make_db_connection()
        self.table=table
        self.update_schema()

    def make_db_connection(self):
        load_dotenv()
        MYSQLUSER=os.getenv('DB_USER')
        MYSQLPASSWORD=os.getenv('DB_PASSWORD')
        MYSQLHOST=os.getenv('DB_HOSTNAME')
        MYSQLDATABASE=os.getenv('DB_NAME')
        MYSQLPORT=os.getenv('DB_PORT')

        try:
            self.cnx = create_engine(url=f"mysql+pymysql://{MYSQLUSER}:{urllib.parse.quote_plus(MYSQLPASSWORD)}@{urllib.parse.quote_plus(MYSQLHOST)}:{MYSQLPORT}/{MYSQLDATABASE}")
                                            
        except Exception as e:
            print("Error {e}")
            raise ConnectionError(e)
        
        if self.cnx:
            try:
                self.cnx.connect()
                print('connection successful')
            except Exception as e:
                print("Error {e}")
                raise ConnectionError(e)

    def update_schema(self):
        """Update the database schema if needed."""
        # Skip schema updates since we'll work with the existing schema
        print("Using existing database schema")
        return

    def push_image(self, image_path, project_id):
        """Push an image to the database."""
        try:
            connection = self.cnx.connect()
            
            # Generate a unique ID for the image
            image_id = int(uuid.uuid4().int % 2147483647)  # Use integer ID to match schema
            
            # Insert only the image ID and project ID - no image_path field
            command = """
            INSERT INTO OriginalImages (ImageID, ProjectID)
            VALUES (:image_id, :project_id)
            """
            
            # Execute the command with parameters
            result = connection.execute(
                text(command),
                {
                    "image_id": image_id,
                    "project_id": project_id
                }
            )
            
            connection.commit()
            print(f"Successfully added image with ID: {image_id}")
            return image_id
            
        except Exception as e:
            print(f"Error adding image: {e}")
            return None
        finally:
            connection.close()

    def push_label(self, label:Label):
        """Push a label to the database."""
        try:
            connection = self.cnx.connect()
            
            # Get the important fields and make sure they match the schema
            image_id = label.get("image_id")
            x1 = label.get("x1")
            y1 = label.get("y1")
            x2 = label.get("x2")
            y2 = label.get("y2")
            confidence = label.get("confidence", 0.0)
            
            # Insert into Labels table with only the columns we need
            command = """
            INSERT INTO Labels (ImageID, X1, Y1, X2, Y2, Confidence)
            VALUES (:image_id, :x1, :y1, :x2, :y2, :confidence)
            """
            
            result = connection.execute(
                text(command),
                {
                    "image_id": image_id,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": confidence
                }
            )
            
            connection.commit()
            print("Successfully added label")
            return result.lastrowid
            
        except Exception as e:
            print(f"Error adding label: {e}")
            return None
        finally:
            connection.close()

    def get_labels(self, query:str) -> list[Label]:
        self.make_db_connection()
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results")
                for res in result:
                    l = Label(
                        LabelID=res[0],
                        LabellerID=res[1],
                        ImageID=res[2],
                        Class=res[3],
                        top_left_x=res[4],
                        top_left_y=res[5],
                        bot_right_x=res[6],
                        bot_right_y=res[7],
                        offset_x=res[8],
                        offset_y=res[9],
                        creation_time=res[10],
                        origImageID=res[11]
                    )
                    results.append(l)
                return results
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            

    
# LD = MYSQLLabelDatabaseConnector()       

# l = Label(
#     None, 1,1,"test", 34,34,64,64,0,0,1010
# )
# LD.push_label(l)
# print(LD.get_labels("SELECT * FROM my_image_db.Labels;"))