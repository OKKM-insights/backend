from abc import ABC, abstractmethod
import os
import io
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

from services.DataTypes import Project, Image
import urllib.parse
import pymysql
from PIL import Image as pilImage


class ProjectDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass


    @abstractmethod
    def get_projects(self, query:str) -> list[Project]:
        pass

class NoneDB(ProjectDatabaseConnector):


    def make_db_connection(self):
        pass


    def get_projects(self, query:str) -> list[Project]:
        pass

class MYSQLProjectDatabaseConnector(ProjectDatabaseConnector):

    def __init__(self, table:str='Projects'):
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


    def get_projects(self, query:str) -> list[Project]:
        # query should be something like 'where id = x' or 'where skill = 'x''
        self.make_db_connection()
        projects = []
        project_ids = []
        categories = []
        end_dates = []

        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                for res in result:
                    project_ids.append(res[0])
                    categories.append(res[5].split(','))
                    end_dates.append(res[4])
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
            print(project_ids)
            print(categories)


            query = text("""
            SELECT * FROM OriginalImages WHERE projectId = :project_id;
        """)


            try:
                for i, id in enumerate(project_ids):
                    images = []
                    data = {
                        "project_id": id
                    }
                    result = connection.execute(query, data)
                    print(f"Query returned {result.rowcount} results") 

                    for res in result:
                        images.append(Image(res[0], res[1], pilImage.open(io.BytesIO(res[2]))))
                    projects.append(Project(id, categories[i], images.copy(), end_dates[i]))
            except Exception as e:
                print("Error {e}")
                raise Exception(e)
        return projects
    
            

    
# LD = MYSQLProjectDatabaseConnector()       





# projects = LD.get_projects("SELECT * FROM my_image_db.Projects;")
# projects[4].images[0].image_data.save('tmp_img.png')
# print(projects[4].classes)