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
from services.DataTypes import ImageClassMeasure, Label
import urllib.parse
import pymysql
import numpy as np
import matplotlib.pyplot as plt


class ImageClassMeasureDatabaseConnector(ABC):

    @abstractmethod
    def make_db_connection(self):
        pass

    @abstractmethod
    def push_imageclassmeasure(self, imageclassmeasure:ImageClassMeasure):
        pass

    @abstractmethod
    def get_imageclassmeasures(self, query:str) -> list[ImageClassMeasure]:
        pass

class NoneDB(ImageClassMeasureDatabaseConnector):


    def make_db_connection(self):
        pass


    def push_imageclassmeasure(self, imageclassmeasure:ImageClassMeasure):
        pass


    def get_imageclassmeasures(self, query:str) -> list[ImageClassMeasure]:
        pass

class MYSQLImageClassMeasureDatabaseConnector(ImageClassMeasureDatabaseConnector):

    def __init__(self, table:str='ImageClassMeasure'):
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


    def push_imageclassmeasure(self, imageclassmeasure:ImageClassMeasure):

        query_imageclassmeasure_db = text("""
            INSERT INTO ImageClassMeasure (ImageID, x, y, label, likelihood, confidence, helpervalue_1, helpervalue_2, im_height, im_width) 
            VALUES (:ImageID, :x, :y, :label, :likelihood, :confidence, :helpervalue_1, :helpervalue_2, :im_height, :im_width)
            ON DUPLICATE KEY UPDATE 
            likelihood = VALUES(likelihood),
            confidence = VALUES(confidence),
            helpervalue_1 = VALUES(helpervalue_1),
            helpervalue_2 = VALUES(helpervalue_2);
        """)



        with self.cnx.connect() as connection:
            try:
                # Collect all rows before executing the query
                batch_data = []

                for y in range(imageclassmeasure.im_height):
                    for x in range(imageclassmeasure.im_width):
                        batch_data.append({
                            "ImageID": imageclassmeasure.imageID,
                            "x": x,
                            "y": y,
                            "label": imageclassmeasure.label,
                            "likelihood": imageclassmeasure.likelihoods[x][y],
                            "confidence": imageclassmeasure.confidence[x][y],
                            "helpervalue_1": imageclassmeasure.helper_values[x][y][0],
                            "helpervalue_2": imageclassmeasure.helper_values[x][y][1],
                            "im_height": imageclassmeasure.im_height,
                            "im_width": imageclassmeasure.im_width
                        })

                # Execute all at once using `executemany()`
                connection.execute(query_imageclassmeasure_db, batch_data)
                
                connection.commit()
                print("Query successful")
            except Exception as e:
                print(f"Error: {e}")
                raise Exception(e)

    def push_imageclassmeasure_images(self, imageclassmeasure:ImageClassMeasure):

        query_imageclassmeasure_db = text("""
            INSERT INTO ImageClassMeasure_images (ImageID, label, likelihood, confidence, helpervalue_1, helpervalue_2, im_height, im_width) 
            VALUES (:ImageID, :label, :likelihood, :confidence, :helpervalue_1, :helpervalue_2, :im_height, :im_width)
            ON DUPLICATE KEY UPDATE 
            likelihood = VALUES(likelihood),
            confidence = VALUES(confidence),
            helpervalue_1 = VALUES(helpervalue_1),
            helpervalue_2 = VALUES(helpervalue_2);
        """)



        with self.cnx.connect() as connection:
            helper_values_1 = [[pixel[0] for pixel in row] for row in imageclassmeasure.helper_values]
            helper_values_2 = [[pixel[1] for pixel in row] for row in imageclassmeasure.helper_values]

            try:
                # plt.imshow(np.array(imageclassmeasure.confidence, dtype=np.float16))
                # plt.savefig("temp.jpeg")
                data = {
                            "ImageID": imageclassmeasure.imageID,
                            "label": imageclassmeasure.label,
                            "likelihood": np.array(imageclassmeasure.likelihoods, dtype=np.float16).tobytes(),
                            "confidence": np.array(imageclassmeasure.confidence, dtype=np.float16).tobytes(),
                            "helpervalue_1":np.array(helper_values_1, dtype=np.float16).tobytes(),
                            "helpervalue_2":np.array(helper_values_2, dtype=np.float16).tobytes(),
                            "im_height": imageclassmeasure.im_height,
                            "im_width": imageclassmeasure.im_width
                        }


                connection.execute(query_imageclassmeasure_db, data)
                
                connection.commit()
                print("Query successful")
            except Exception as e:
                print(f"Error: {e}")
                raise Exception(e)
            

    def get_imageclassmeasures(self, query:str) -> ImageClassMeasure:
        # --only request one object at a time please 😭🙏--
        self.make_db_connection()

        imageID= ''
        x = []
        y = []
        label = ''
        likelihoods =[]
        confidences =[]
        helpervalue_1 = []
        helpervalue_2 = []
        im_height = 0
        im_width = 0
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                if result.rowcount == 0:
                    return None
                for res in result:
                    imageID = res[0]
                    x.append(res[1])
                    y.append(res[2])
                    label = res[3]
                    likelihoods.append(res[4])
                    confidences.append(res[5])
                    helpervalue_1.append(res[6])
                    helpervalue_2.append(res[7])
                    im_height = res[8]
                    im_width = res[9]

            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
            print(imageID)

            likelihoods_ordered = [[0.5] * im_width for _ in range(im_height)]
            confidence_ordered = [[0.0] * im_width for _ in range(im_height)]
            helper_values_ordered = [[[0.5,0.5] for _ in range(im_width)] for _ in range(im_height)]

            for i in range(im_height*im_width):
                likelihoods_ordered[y[i]][x[i]] =  likelihoods[i]
                confidence_ordered[y[i]][x[i]] = confidences[i]
                helper_values_ordered[y[i]][x[i]][0] = helpervalue_1[i]
                helper_values_ordered[y[i]][x[i]][1] = helpervalue_2[i]
            
        icm = ImageClassMeasure(imageID, likelihoods_ordered, confidence_ordered, helper_values_ordered, label, im_width, im_height)
        return icm
    
    def get_imageclassmeasures_images(self, query:str) -> ImageClassMeasure:
        # --only request one object at a time please 😭🙏--
        self.make_db_connection()

        imageID= ''
        label = ''
        likelihoods = None
        confidence = None
        helper_value_1 = None
        helper_value_2 = None
        im_height = 0
        im_width = 0
        with self.cnx.connect() as connection:
            try:
                result = connection.execute(text(query))
                print(f"Query returned {result.rowcount} results") 
                if result.rowcount == 0:
                    return None
                for res in result:
                    imageID = res[0]
                    label = res[1]
                    im_height = res[6]
                    im_width = res[7]
                    likelihoods = np.frombuffer(res[2], dtype=np.float16).reshape((im_height, im_width, 1)).tolist()
                    confidence= np.frombuffer(res[3], dtype=np.float16).reshape((im_height, im_width, 1)).tolist()
                    helper_value_1 = np.frombuffer(res[4], dtype=np.float16).reshape((im_height, im_width, 1))
                    helper_value_2 = np.frombuffer(res[5], dtype=np.float16).reshape((im_height, im_width, 1))
                    

            except Exception as e:
                print("Error {e}")
                raise Exception(e)
            
            print(imageID)

            helper_values = np.stack((helper_value_1.reshape(im_width, im_height), helper_value_2.reshape(im_width, im_height)), axis=-1).tolist()

            
            
        icm = ImageClassMeasure(imageID, likelihoods, confidence, helper_values, label, im_width, im_height)
        return icm
            
            
    
      

    
# LD = MYSQLImageClassMeasureDatabaseConnector()       

# l = Label('08500f1e-9eff-4d1a-8d9c-1f1d0a2a2bd6','t','t','class',0,0,0,0,0,0,'0')

# I = ImageClassMeasure('test', None, None, None, 'label', 400, 400)

# LD.push_imageclassmeasure(I)
# res = LD.get_imageclassmeasures("SELECT * FROM ImageClassMeasure Where ImageID = 'test2' and Label = 'label';")
# print(res.likelihoods)