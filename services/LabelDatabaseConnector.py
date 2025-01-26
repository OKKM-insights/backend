from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from Label import Label


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

    def __init__(self, table:str='labels'):
        self.cnx = None
        self.make_db_connection()
        self.table=table

    def initialize_connection(self):
        load_dotenv()
        MYSQLUSER=os.getenv('_LABELDATABASE_MYSQLUSER')
        MYSQLPASSWORD=os.getenv('_LABELDATABASE_MYSQLPASSWORD')
        MYSQLHOST=os.getenv('_LABELDATABASE_MYSQLHOST')
        MYSQLDATABASE=os.getenv('_LABELDATABASE_MYSQLDATABASE')

        try:
            self.cnx = create_engine(url=f"mysql+pymysql://{MYSQLUSER}@{MYSQLPASSWORD}:{MYSQLHOST}/{MYSQLDATABASE}")
                                            
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
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(
                    text(f"INSERT INTO {self.table} VALUES ({uuid.uuid4(),
                                                             Label.LabellerID, 
                                                             Label.ImageID,
                                                             Label.Class,
                                                             Label.RelatedPixels})")
                )
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)

    def get_labels(self, query:str) -> list[Label]:
        
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {len(result)} results")
                return list(result)
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            

    
            