from ProjectDatabaseConnector import ProjectDatabaseConnector, MYSQLProjectDatabaseConnector
from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from LabellerDatabaseConnector import LabellerDatabaseConnector, MYSQLLabellerDatabaseConnector
from ImageObjectDatabaseConnector import ImageObjectDatabaseConnector, MYSQLImageObjectDatabaseConnector
from ObjectExtractionService import ObjectExtractionService
from ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector


class ObjectExtractionManager():


    def __init__(self,
                 project_db: ProjectDatabaseConnector,
                 label_db: LabelDatabaseConnector,
                 labeller_db: LabellerDatabaseConnector,
                 imageobject_db: ImageObjectDatabaseConnector,
                 object_service: ObjectExtractionService):
        self.project_db = project_db
        self.label_db = label_db
        self.labeller_db = labeller_db
        self.imageobject_db = imageobject_db
        self.object_service = object_service
        
    
    def get_objects(self, project_id, Class):
        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"

        project = self.project_db.get_projects(query_projects)[0]
        objects = []
        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (ImageID = {image.ImageID}) and (Class = '{Class}');"
            labels = self.label_db.get_labels(query_labels)
            print(f"found {len(labels)} labels")
            labeller_ids = set()
            for label in labels:
                labeller_ids.add(label.LabellerID)
            query_labellers = f"SELECT * FROM my_image_db.Labeller_skills WHERE Labeller_id IN ({tuple(labeller_ids)});"
            labellers = self.labeller_db.get_labellers(query_labellers)
            
            objects.append(self.object_service.get_objects(image, Class, labellers, labels))

        for object_list in objects:
            for ob in object_list:
                self.imageobject_db.push_imageobject(ob)



t = ObjectExtractionManager(MYSQLProjectDatabaseConnector(),MYSQLLabelDatabaseConnector(), MYSQLLabellerDatabaseConnector(), MYSQLImageObjectDatabaseConnector(), ObjectExtractionService(MYSQLImageClassMeasureDatabaseConnector(), MYSQLLabellerDatabaseConnector()))
t.get_objects('5', 'plane')

