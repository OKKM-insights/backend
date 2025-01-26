from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
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

class MYSQLDB(LabelDatabaseConnector):

    def __init__(self):
        self.cnx = None
        self.make_db_connection()

    def initialize_connection(self):
        load_dotenv()
        MYSQLUSER=os.getenv('_LABELDATABASE_MYSQLUSER')
        MYSQLPASSWORD=os.getenv('_LABELDATABASE_MYSQLPASSWORD')
        MYSQLHOST=os.getenv('_LABELDATABASE_MYSQLHOST')
        MYSQLDATABASE=os.getenv('_LABELDATABASE_MYSQLDATABASE')

        try:
            self.cnx = create_engine(url="mysql+pymysql://{MYSQLUSER}@{MYSQLPASSWORD}:{MYSQLHOST}/{MYSQLDATABASE}")
                                            
        except Exception as e:
            raise ConnectionError(e)
        
        if self.cnx:
            try:
                self.cnx.connect()
                print('connection successful')
            except Exception as e:
                raise ConnectionError(e)


    def push_label(self, label:Label):
        pass

    def get_labels(self, query:str) -> list[Label]:
        pass

    def save_map(self, data: dict) -> bool:
        """
        Save a map design as a feature collection according to database schema
        """
        if not self.cnx.is_connected():
            try:
                self.initialize_connection()
            except mysql.connector.Error as e:
                raise ConnectionError(e)
            
        cursor = self.cnx.cursor()

        add_collection = ("INSERT INTO feature_collections "
                          "VALUES (%s, %s, %s, %s)")
        add_feature = ("INSERT INTO features "
                       "VALUES (%s, %s, %s, %s, ST_GeomFromGeoJSON(%s))")

        collection_id = uuid.uuid4()
        creation_date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        creation_source = None
        is_shared = False

        try:
            creation_source = data['creation_source']
        except KeyError:
            print('no creation source supplied')

        try:
            is_shared = data['is_shared']
        except KeyError:
            print('no sharing permissions supplied')
            raise KeyError('no sharing permissions supplied')

        try:
            features = data['geojson']['features']
        except KeyError:
            raise KeyError('No features supplied')
        
 
        cursor.execute(add_collection, (str(collection_id), creation_date, creation_source, 1 if is_shared == 'true' else 0))

        for feature in features:
            feature_id = uuid.uuid4()
            try:
                geometry_type = feature['geometry']['type']
            except KeyError:
                raise KeyError('Missing geometry or type')
                
            
            try:
                feature_type = feature['properties']['feature_type']
            except KeyError:
                raise KeyError('Missing properties or feature_type')
                
            
            try:
                geometry = feature['geometry']
            except KeyError:
                raise KeyError('Missing geometry')
                
            
            cursor.execute(add_feature, (str(feature_id), str(collection_id), geometry_type, feature_type, json.dumps(geometry)))

        self.cnx.commit()
        cursor.close()
            