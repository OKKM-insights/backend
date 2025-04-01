from ProjectDatabaseConnector import ProjectDatabaseConnector, MYSQLProjectDatabaseConnector
from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from LabellerDatabaseConnector import LabellerDatabaseConnector, MYSQLLabellerDatabaseConnector
from ImageObjectDatabaseConnector_bb import ImageObjectDatabaseConnector_bb, MYSQLImageObjectDatabaseConnector_bb
from ObjectExtractionService import ObjectExtractionService
from ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector
from DataTypes import Labeller
import time

class ObjectExtractionManager():


    def __init__(self,
                 project_db: ProjectDatabaseConnector,
                 label_db: LabelDatabaseConnector,
                 labeller_db: LabellerDatabaseConnector,
                 imageobject_db: ImageObjectDatabaseConnector_bb,
                 object_service: ObjectExtractionService):
        self.project_db = project_db
        self.label_db = label_db
        self.labeller_db = labeller_db
        self.imageobject_db = imageobject_db
        self.object_service = object_service
        
    
    def get_objects(self, project_id, Class, demo=False):
        t = time.time()
        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"

        project = self.project_db.get_projects(query_projects)[0]
        objects = []
        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (OrigImageID = {image.ImageID}) and (Class = '{Class}');"
            labels = self.label_db.get_labels(query_labels)
            print(f"found {len(labels)} labels")
            labeller_ids = set()
            for label in labels:
                labeller_ids.add(label.LabellerID)

            query_labellers = f"SELECT * FROM my_image_db.Labeller_skills WHERE Labeller_id IN :ids"

            labellers = self.labeller_db.get_labellers_with_data(query_labellers, {'ids': tuple(labeller_ids)})

            found_labeller_ids = [labeller.LabellerID for labeller in labellers]
            for labeller_id in labeller_ids:
                if labeller_id not in found_labeller_ids:
                    labellers.append(Labeller(labeller_id, Class))

            print(labellers)
            print(labels[0].__dict__)

            objects.append(self.object_service.get_objects(image, Class, labellers, labels, demo=demo))

        for object_list in objects:
            for ob in object_list:
                self.imageobject_db.push_imageobject(ob)
        print(f"completed in {time.time()-t} seconds")


t = ObjectExtractionManager(MYSQLProjectDatabaseConnector(),MYSQLLabelDatabaseConnector(), MYSQLLabellerDatabaseConnector(), MYSQLImageObjectDatabaseConnector_bb(), ObjectExtractionService(MYSQLImageClassMeasureDatabaseConnector(), MYSQLLabellerDatabaseConnector()))
t.get_objects('66', 'plane', demo=False)

