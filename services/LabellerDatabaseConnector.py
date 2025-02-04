from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from DataTypes import Labeller
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

    @abstractmethod
    def get_labellers_with_data(self, query:str, data) -> list[Labeller]:
        pass

class NoneDB(LabellerDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_labeller(self, labeller:Labeller):
        pass


    def get_labellers(self, query:str) -> list[Labeller]:
        pass

    def get_labellers_with_data(self, query:str, data) -> list[Labeller]:
        pass

class MYSQLLabellerDatabaseConnector(LabellerDatabaseConnector):

    def __init__(self, table:str='Labeller_skills'):
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
        self.make_db_connection()
        query = text("""
            INSERT INTO Labeller_skills (Labeller_id, skill, alpha, beta) 
            VALUES (:labeller_id, :skill, :alpha, :beta)
            ON DUPLICATE KEY UPDATE 
            alpha = VALUES(alpha), 
            beta = VALUES(beta);
        """)


        with self.cnx.connect() as connection:
            try:
                data = {
                    "labeller_id": labeller.LabellerID,
                    "skill": labeller.skill,
                    "alpha": labeller.alpha,
                    "beta": labeller.beta,
                }
                connection.execute(query, data)

                connection.commit()
                print(f"Query sucessful")
            except Exception as e:
                print("Error {e}")
                raise Exception(e)

    def get_labellers(self, query:str) -> list[Labeller]:
        self.make_db_connection()
        # query should be something like 'where id = x' or 'where skill = 'x''
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    results.append(Labeller(res[0], res[1], res[2], res[3]))
                return results
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
    def get_labellers_with_data(self, query:str, data) -> list[Labeller]:
        self.make_db_connection()
        # query should be something like 'where id = x' or 'where skill = 'x''
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query), data)
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    results.append(Labeller(res[0], res[1], res[2], res[3]))
                return results
            except Exception as e:
                print("Error {e}")
                raise Exception(e)   
    
            

    
# LD = MYSQLLabellerDatabaseConnector()       

# l = Labeller(LabellerID='1', skill = 'plane', alpha=1.1, beta=1)


# print(l.LabellerID)
# print(l.skill)
# LD.push_labeller(l)
# print(LD.get_labellers("SELECT * FROM my_image_db.Labeller_skills;"))