from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from DataTypes import Label
from flask import Flask, Response, request
from flask_cors import CORS, cross_origin
import json


class LabelServer():

    def __init__(self, db: LabelDatabaseConnector):
        self.version = '1.0'

        self.db = db
        self.app = Flask(__name__)
        CORS(self.app)

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
            request_data = request.get_json(force=True)
            
        except Exception as e:
            print(e)
            return Response(status=400, response='couldn\'t extract json')
        
        request_headers = request.headers

        
        try:
            for req in request_data['labels']:
                label = Label(LabelID=None,
                        LabellerID=req['LabellerID'], 
                        ImageID=req['ImageID'],
                        Class=req['Class'],
                        bot_right_x=req['bot_right_x'],
                        bot_right_y=req['bot_right_y'],
                        top_left_x=req['top_left_x'],
                        top_left_y=req['top_left_y'],
                        offset_x=req['offset_x'],
                        offset_y=req['offset_y'],
                        creation_time=req['creation_time'],
                        origImageID=req['OrigImageID']
                        )
                self.db.push_label(label=label)

        except ValueError as e:
            return Response(status=400, response=str(e))
        except KeyError as e:
            return Response(status=400, response=str(e))
        except Exception as e:
            print("other Error")
            return Response(status=400, response=str(e))
        
        return Response(status=200, response='all labels saved')

db = MYSQLLabelDatabaseConnector()
server = LabelServer(db)
