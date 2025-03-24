from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import uuid
import time
import datetime
import json
from .DataTypes import Labeller
import urllib.parse
import pymysql
import base64
import subprocess


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
        """Create a database connection."""
        load_dotenv()
        
        # Get database credentials from environment variables
        user = os.getenv('DB_USER', 'admin')
        password = os.getenv('DB_PASSWORD', 'password')
        host = os.getenv('DB_HOSTNAME', 'localhost')
        database = os.getenv('DB_NAME', 'my_image_db')
        port = os.getenv('DB_PORT', '3306')
        
        try:
            # Create the connection URL with proper encoding
            connection_url = f"mysql+pymysql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{database}"
            self.cnx = create_engine(connection_url)
            
            # Test the connection
            with self.cnx.connect() as connection:
                print('Database connection successful')
                
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            raise


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
            

    def get_labeller_info_with_data(self, query:str, data) -> list[Labeller]:
        self.make_db_connection()
        # query should be something like 'where id = x' or 'where skill = 'x''
        results = []
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query), data)
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    results.append({'profile_picture': base64.b64encode(res[2]).decode('utf-8') if res[2] else None,
                                    'first_name': res[3],
                                     'creation_date': str(res[7])})
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

subprocess.run("cmd /c \"mysql -u Kartik -p my_image_db < backend/sql/update_icm_schema.sql\"", shell=True)
