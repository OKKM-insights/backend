from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
from services.DataTypes import ImageObject, Label
import urllib.parse
import pymysql


class ImageObjectDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_imageobject(self, imageobject:ImageObject):
        pass

    @abstractmethod
    def get_imageobjects(self, query:str) -> list[ImageObject]:
        pass

class NoneDB(ImageObjectDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_imageobject(self, imageobject:ImageObject):
        pass


    def get_imageobjects(self, query:str) -> list[ImageObject]:
        pass

class MYSQLImageObjectDatabaseConnector(ImageObjectDatabaseConnector):

    def __init__(self, table:str='ImageObjects'):
        self.cnx = None
        self.make_db_connection()
        self.table=table

    def make_db_connection(self):
        load_dotenv()
        MYSQLUSER=os.getenv('_LABELDATABASE_MYSQLUSER')
        MYSQLPASSWORD=os.getenv('_LABELDATABASE_MYSQLPASSWORD')
        MYSQLHOST=os.getenv('_LABELDATABASE_MYSQLHOST')
        MYSQLDATABASE=os.getenv('_LABELDATABASE_MYSQLDATABASE')

        try:
            self.cnx = create_engine(
    url=f"mysql+pymysql://{str(MYSQLUSER)}:{urllib.parse.quote_plus(str(MYSQLPASSWORD))}"
        f"@{urllib.parse.quote_plus(str(MYSQLHOST))}/{MYSQLDATABASE}"
)
                                            
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


    def push_imageobject(self, imageobject:ImageObject):

        query_imageobject_db = text("""
            INSERT INTO ImageObjects (ImageObjectID, ImageID, Class, Confidence) 
            VALUES (:ImageObjectID, :ImageID, :Class, :Confidence)
            ON DUPLICATE KEY UPDATE 
            Confidence = VALUES(Confidence);
        """)

        query_related_pixels = text("""
            INSERT IGNORE INTO Pixels_in_ImageObject (ImageObjectID, x, y) 
            VALUES (:ImageObjectID, :x, :y);
        """)

        query_related_labels = text("""
            INSERT IGNORE INTO Labels_ImageObjects (ImageObjectID, LabelID) 
            VALUES (:ImageObjectID, :LabelID);
        """)


        with self.cnx.connect() as connection:
            try:
                data_imageobject_db = {
                    "ImageObjectID": imageobject.ImageObjectID,
                    "ImageID": imageobject.ImageID,
                    "Class": imageobject.Class,
                    "Confidence": imageobject.Confidence,
                }

                connection.execute(query_imageobject_db, data_imageobject_db)

                for pixel in imageobject.related_pixels:
                    data_related_pixels = {
                        "ImageObjectID": imageobject.ImageObjectID,
                        "x": pixel[0],
                        "y": pixel[1],
                    }   
                    connection.execute(query_related_pixels, data_related_pixels)

                for label in imageobject.related_labels:
                    data_related_labels = {
                        "ImageObjectID": imageobject.ImageObjectID,
                        "LabelID": label.LabelID
                    }   
                    connection.execute(query_related_labels, data_related_labels)

                connection.commit()
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)

    def get_imageobjects(self, query:str) -> list[ImageObject]:
        self.make_db_connection()

        ImageObjects = []
        ImageObjectIDs = []
        ImageIDs= []
        Classes = []
        Confidences = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    ImageObjectIDs.append(res[0])
                    ImageIDs.append(res[1])
                    Classes.append(res[2])
                    Confidences.append(res[3])
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
            print(ImageObjectIDs)

            # --- get label ids and ---

            query_label_ids = text("""
                                SELECT * FROM Labels WHERE LabelID in 
                                (SELECT LabelID FROM my_image_db.Labels_ImageObjects WHERE ImageObjectID = :imageobjectid);
                                   """)
            query_pixels = text("""SELECT x,y FROM Pixels_in_ImageObject WHERE ImageObjectID = :imageobjectid;
                                """)

            try:
                for i , id in enumerate(ImageObjectIDs):
                    data = {"imageobjectid": id}
                    labels = self.get_labels(query_label_ids, data)
                    pixels = []
                    result = connection.execute(query_pixels, data)
                    for res in result:
                        pixels.append([res[0], res[1]])
                    ImageObjects.append(ImageObject(id, ImageIDs[i], Classes[i], Confidences[i], pixels.copy(), labels.copy()))
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
        return ImageObjects
            
            
    
    def get_labels(self, query:str, data) -> list[Label]:
        self.make_db_connection()
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(query, data)
                print(f"Query returned {result.rowcount} results")
                for res in result:
                    l = Label(
                        LabelID=res[0],
                        LabellerID=res[1],
                        ImageID=res[2],
                        Class=res[4],
                        top_left_x=res[5],
                        top_left_y=res[6],
                        bot_right_x=res[7],
                        bot_right_y=res[8],
                        offset_x=res[9],
                        offset_y=res[10]
                    )
                    results.append(l)
                return results
            except Exception as e:
                print("Error {e}")
                raise Exception(e)        

    
# LD = MYSQLImageObjectDatabaseConnector()       

# l = Label('08500f1e-9eff-4d1a-8d9c-1f1d0a2a2bd6','t','t','class',0,0,0,0,0,0,'0')

# I = ImageObject('test', 't', 't', 0.1, [[0,0],[0,1],[0,2],[0,3]], [l])

# LD.push_imageobject(I)
# res = LD.get_imageobjects("SELECT * FROM ImageObjects;")
# print(res[0].related_labels)