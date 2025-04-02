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
from services.DataTypes import ImageObject_bb, Label
import urllib.parse
import pymysql


class ImageObjectDatabaseConnector_bb(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_imageobject(self, imageobject:ImageObject_bb):
        pass

    @abstractmethod
    def get_imageobjects(self, query:str) -> list[ImageObject_bb]:
        pass

class NoneDB(ImageObjectDatabaseConnector_bb):


    def make_db_connection(self):
        pass


    def push_imageobject(self, imageobject:ImageObject_bb):
        pass


    def get_imageobjects(self, query:str) -> list[ImageObject_bb]:
        pass

class MYSQLImageObjectDatabaseConnector_bb(ImageObjectDatabaseConnector_bb):

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


    def push_imageobject(self, imageobject:ImageObject_bb):

        query_imageobject_db = text("""
            INSERT INTO ImageObjects_bb (ImageObjectID, ImageID, Class, Confidence, top_left_x, top_left_y, bot_right_x, bot_right_y) 
            VALUES (:ImageObjectID, :ImageID, :Class, :Confidence, :top_left_x, :top_left_y, :bot_right_x, :bot_right_y)
            ON DUPLICATE KEY UPDATE 
            Confidence = VALUES(Confidence);
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
                    "top_left_x": imageobject.top_left_x,
                    "top_left_y": imageobject.top_left_y,
                    "bot_right_x": imageobject.bot_right_x,
                    "bot_right_y": imageobject.bot_right_y,
                                   }

                connection.execute(query_imageobject_db, data_imageobject_db)


                connection.commit()
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)

    def get_imageobjects(self, query:str) -> list[ImageObject_bb]:
        self.make_db_connection()

        ImageObjects = []
        ImageObjectIDs = []
        ImageIDs= []
        Classes = []
        Confidences = []
        coords = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    ImageObjectIDs.append(res[0])
                    ImageIDs.append(res[1])
                    Classes.append(res[2])
                    Confidences.append(res[3])
                    coords.append([res[4],res[5],res[6],res[7]])
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
            print(ImageObjectIDs)

            # --- get label ids and ---

            query_label_ids = text("""
                                SELECT * FROM Labels WHERE LabelID in 
                                (SELECT LabelID FROM my_image_db.Labels_ImageObjects WHERE ImageObjectID = :imageobjectid);
                                   """)
            

            try:
                for i , id in enumerate(ImageObjectIDs):
                    data = {"imageobjectid": id}
                    labels = self.get_labels(query_label_ids, data)
                    ImageObjects.append(ImageObject_bb(id, ImageIDs[i], Classes[i], Confidences[i], coords[i][0],coords[i][1],coords[i][2],coords[i][3], ))
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