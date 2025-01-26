from database_manager import DatabaseManager

from flask import Flask, Response, request
import json


class FlaskServer():

    def __init__(self, db: DatabaseManager):
        self.version = '1.0'

        self.db = db
        self.image_renderer = image_renderer
        self.app = Flask(__name__)
        CORS(self.app)

        self.app.add_url_rule(
            rule=f'/{self.version}/savemap'
            ,endpoint=f'/{self.version}/savemap'
            ,view_func=self.save_map
            ,methods=['POST']
        )
        self.app.add_url_rule(
            rule=f'/{self.version}/mailmap'
            ,endpoint=f'/{self.version}/mailmap'
            ,view_func=self.mail_map
            ,methods=['POST']
        )
        self.app.run()

    def save_map(self) -> Response:
        '''
        save map modifications to table in database
        '''
        try:
            request_data = request.json
        except:
            return Response(status=400, response='couldn\'t extract json')
        request_headers = request.headers

        try:
            self.db.save_map(request_data)

        except ValueError as e:
            return Response(status=400, response=str(e))
        except KeyError as e:
            return Response(status=400, response=str(e))
        except:
            print("other Error")
            return Response(status=400, response=str(e))
        
        return Response(status=200)
        

    def mail_map(self) -> Response:
        '''
        render map image from GEO JSON, and mail to provided email address
        '''
        request_data = request.json
        request_headers = request.headers

        B64_img = self.image_renderer.render_image(request_data)

        return Response(status=200)


        