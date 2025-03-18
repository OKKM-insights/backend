from ProjectDatabaseConnector import ProjectDatabaseConnector, MYSQLProjectDatabaseConnector
from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from LabellerDatabaseConnector import LabellerDatabaseConnector, MYSQLLabellerDatabaseConnector
from ImageObjectDatabaseConnector import ImageObjectDatabaseConnector, MYSQLImageObjectDatabaseConnector
from ObjectExtractionService import ObjectExtractionService
from ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector
import json

class ReportGenerator():

    def __init__(self):
        self.ProjectDatabaseConnector = MYSQLProjectDatabaseConnector()
        self.LabelDatabaseConnector = MYSQLLabelDatabaseConnector()
        self.ImageObjectDatabaseConnector = MYSQLImageObjectDatabaseConnector()
        self.LabellerDatabaseConnector = MYSQLLabellerDatabaseConnector()
        self.ICMDB = MYSQLImageClassMeasureDatabaseConnector()

    def get_report_info(self, project_id) -> dict:
        num_labels = 0
        num_images = 0
        num_labellers = 0
        avg_num_labels = 0 
        label_count = dict()
        labeller_ids = set()

        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"
        project = self.ProjectDatabaseConnector.get_projects(query_projects)[0]

        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (OrigImageID = {image.ImageID});"
            labels = self.LabelDatabaseConnector.get_labels(query_labels)
            print(f"found {len(labels)} labels")
            
            for label in labels:
                labeller_ids.add(label.LabellerID)
                if label.LabellerID in label_count:
                    label_count[label.LabellerID] += 1
                else:
                    label_count[label.LabellerID] = 1

            print(label_count)

            

            
            
            num_labels += len(labels)
            num_labellers += len(labeller_ids)
            
            print(labels[0].__dict__)

        top_3_labellers = sorted(label_count, key=label_count.get, reverse=True)[:3]

        query_labellers = f"SELECT * FROM my_image_db.Labellers WHERE id IN :ids"
        labellers = self.LabellerDatabaseConnector.get_labeller_info_with_data(query_labellers, {'ids': tuple(top_3_labellers)})
        print(labellers)
        print(top_3_labellers)
        num_images = len(project.images)
        avg_num_labels = (num_labels / num_images) / num_labellers

        user_label_count = [0,0,0]
        user_info = [None, None, None]
        try:
            user_label_count[0] = label_count[top_3_labellers[0]]
            user_info[0] = labellers[0]
        except:
            user_label_count[0] = None
            user_info[0] = None

        try:
            user_label_count[1] = label_count[top_3_labellers[1]]
            user_info[1] = labellers[1]
        except:
            user_label_count[1] = None
            user_info[1] = None

        try:
            user_label_count[2] = label_count[top_3_labellers[2]]
            user_info[2] = labellers[2]
        except:
            user_label_count[2] = None
            user_info[2] = None

        response = {
            'num_labels': num_labels,
            'num_labellers': num_labellers,
            'num_images': num_images,
            'avg_num_labels': avg_num_labels,
            'top_labellers':{
                '1': {
                    'num_labels': user_label_count[0],
                    'user_info': user_info[0]
                },
                '2': {
                    'num_labels': user_label_count[1],
                    'user_info': user_info[1]
                },
                '3': {
                    'num_labels': user_label_count[2],
                    'user_info': user_info[2]
                },
            }
        }
        return json.dumps(response)


            



# r = ReportGenerator()
# print(r.get_report_info(14))

