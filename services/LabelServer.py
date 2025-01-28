from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from services.DataTypes import Label
from flask import Flask, Response, request
import json


class LabelServer():

    def __init__(self, db: LabelDatabaseConnector):
        self.version = '1.0'

        self.db = db
        self.app = Flask(__name__)


        self.app.add_url_rule(
            rule=f'/{self.version}/push_label'
            ,endpoint=f'/{self.version}/push_label'
            ,view_func=self.push_label
            ,methods=['POST']
        )
        self.app.run()

       

    def push_label(self) -> Response:
        '''
        save map modifications to table in database
        '''
        try:
            request_data = request.json
        except:
            return Response(status=400, response='couldn\'t extract json')
        
        request_headers = request.headers

        label = Label(LabelID=None,
                      LabellerID=request_data['LabellerID'], 
                      ImageID=request_data['ImageID'],
                      Class=request_data['Class'],
                      bot_right_x=request_data['bot_right_x'],
                      bot_right_y=request_data['bot_right_y'],
                      top_left_x=request_data['top_left_x'],
                      top_left_y=request_data['top_left_y'],
                      offset_x=request_data['offset_x'],
                      offset_y=request_data['offset_y'],
                      creation_time=request_data['creation_time']
                      )
        try:
            self.db.push_label(label=label)

        except ValueError as e:
            return Response(status=400, response=str(e))
        except KeyError as e:
            return Response(status=400, response=str(e))
        except:
            print("other Error")
            return Response(status=400, response=str(e))
        
        return Response(status=200)

db = MYSQLLabelDatabaseConnector()
server = LabelServer(db)
