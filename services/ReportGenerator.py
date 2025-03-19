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
        label_count_by_labeller = dict()
        label_count_by_class = dict()
        labeller_ids = set()
        end_time = "0"
        last_label_time = "0"

        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"
        project = self.ProjectDatabaseConnector.get_projects(query_projects)[0]

        end_time = str(project.end_date)

        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (OrigImageID = {image.ImageID}) Order BY creation_time DESC;"
            labels = self.LabelDatabaseConnector.get_labels(query_labels)
            
            print(f"found {len(labels)} labels")
            try:
                last_label_time = str(labels[0].creation_time)
            except:
                pass

            for label in labels:
                labeller_ids.add(label.LabellerID)

                if label.Class in label_count_by_class:
                    label_count_by_class[label.Class] += 1
                else:
                    label_count_by_class[label.Class] = 1

                if label.LabellerID in label_count_by_labeller:
                    label_count_by_labeller[label.LabellerID] += 1
                else:
                    label_count_by_labeller[label.LabellerID] = 1

            print(label_count_by_labeller)

            

            
            
            num_labels += len(labels)
            num_labellers += len(labeller_ids)
            
           

        top_3_labellers = sorted(label_count_by_labeller, key=label_count_by_labeller.get, reverse=True)[:3]

        if top_3_labellers:
            query_labellers = f"SELECT * FROM my_image_db.Labellers WHERE id IN :ids"
            labellers = self.LabellerDatabaseConnector.get_labeller_info_with_data(query_labellers, {'ids': tuple(top_3_labellers)})
        num_images = len(project.images)
        if num_labels > 0:
            avg_num_labels = (num_labels / num_images) / num_labellers

        user_label_count = [0,0,0]
        user_info = [None, None, None]
        try:
            user_label_count[0] = label_count_by_labeller[top_3_labellers[0]]
            user_info[0] = labellers[0]
        except:
            user_label_count[0] = None
            user_info[0] = None

        try:
            user_label_count[1] = label_count_by_labeller[top_3_labellers[1]]
            user_info[1] = labellers[1]
        except:
            user_label_count[1] = None
            user_info[1] = None

        try:
            user_label_count[2] = label_count_by_labeller[top_3_labellers[2]]
            user_info[2] = labellers[2]
        except:
            user_label_count[2] = None
            user_info[2] = None

        response = {
            'num_labels': num_labels,
            'num_labellers': num_labellers,
            'num_images': num_images,
            'avg_num_labels': avg_num_labels,
            'project_end_date': end_time,
            'last_label_time': last_label_time,
            'category_data': label_count_by_class,
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

