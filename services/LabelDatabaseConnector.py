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

from services.DataTypes import Label
import urllib.parse
import pymysql


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


    def push_label(self, label:Label):
        self.make_db_connection()
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(
                    text(f"""INSERT INTO {self.table} VALUES { label.LabelID,
                                                               label.LabellerID, 
                                                               label.ImageID,
                                                               label.Class,
                                                               label.top_left_x if label.top_left_x else 'NULL',
                                                               label.top_left_y if label.top_left_y else 'NULL',
                                                               label.bot_right_x if label.bot_right_x else 'NULL',
                                                               label.bot_right_y if label.bot_right_y else 'NULL',
                                                               label.offset_x if label.offset_x else 'NULL',
                                                               label.offset_y if label.offset_y else 'NULL',
                                                               label.creation_time,
                                                               label.origImageID}""")
                )
                connection.commit()
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
    def push_labels_batch(self, labels_batch: list):
        query = text("""
            INSERT INTO Labels 
            (LabelID, LabellerID, ImageID, Class, top_left_x, top_left_y, bot_right_x, bot_right_y, offset_x, offset_y, creation_time, origImageID)
            VALUES (:LabelID, :LabellerID, :ImageID, :Class, :top_left_x, :top_left_y, :bot_right_x, :bot_right_y, :offset_x, :offset_y, :creation_time, :origImageID)
            ON DUPLICATE KEY UPDATE 
                top_left_x = VALUES(top_left_x),
                top_left_y = VALUES(top_left_y),
                bot_right_x = VALUES(bot_right_x),
                bot_right_y = VALUES(bot_right_y)
        """)
        with self.cnx.connect() as connection:
            connection.execute(query, labels_batch)
            connection.commit()

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