from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from DataTypes import ImageObject, Label
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
            self.cnx = create_engine(url=f"mysql+pymysql://{MYSQLUSER}:{urllib.parse.quote_plus(MYSQLPASSWORD)}@{urllib.parse.quote_plus(MYSQLHOST)}/{MYSQLDATABASE}")
                                            
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
            INSERT INTO Pixels_in_ImageObject (ImageObjectID, x, y) 
            VALUES (:ImageObjectID, :x, :y);
        """)

        query_related_labels = text("""
            INSERT INTO Labels_ImageObjects (ImageObjectID, LabelID) 
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
        # query should be something like 'where id = x' or 'where skill = 'x''
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    results.append(ImageObject(res[0], res[1], res[2], res[3]))
                return results
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
    
            

    
LD = MYSQLImageObjectDatabaseConnector()       

l = Label('t','t','t','class',0,0,0,0,0,0,'0')

I = ImageObject('test', 't', 't', 0.1, [[0,0],[0,1],[0,2],[0,3]], [l])

LD.push_imageobject(I)