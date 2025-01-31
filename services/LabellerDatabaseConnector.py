from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from services.DataTypes import Labeller
import urllib.parse
import pymysql


class LabellerDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_labeller(self, labeller:Labeller):
        pass

    @abstractmethod
    def get_labellers(self, query:str) -> list[Labeller]:
        pass

class NoneDB(LabellerDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_labeller(self, labeller:Labeller):
        pass


    def get_labellers(self, query:str) -> list[Labeller]:
        pass

class MYSQLLabellerDatabaseConnector(LabellerDatabaseConnector):

    def __init__(self, table:str='Labellers'):
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


    def push_labeller(self, labeller:Labeller):
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(
                    text(f"""INSERT INTO {self.table} VALUES { labeller.LabellerID,
                                                               label.LabellerID, 
                                                               label.ImageID,
                                                               label.Class,
                                                               label.top_left_x,
                                                               label.top_left_y,
                                                               label.bot_right_x,
                                                               label.bot_right_y,
                                                               label.offset_x,
                                                               label.offset_y,
                                                               label.creation_time}""")
                )
                connection.commit()
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)

    def get_labellers(self, query:str) -> list[Labeller]:
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
            

    
# LD = MYSQLLabelDatabaseConnector()       

# l = Label(
#     None, 1,1,"test", 34,34,64,64,0,0,1010
# )
# LD.push_label(l)
# print(LD.get_labels("SELECT * FROM my_image_db.Labels;"))