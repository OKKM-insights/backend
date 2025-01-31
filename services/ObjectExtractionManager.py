from ProjectDatabaseConnector import ProjectDatabaseConnector
from LabelDatabaseConnector import LabelDatabaseConnector
from LabellerDatabaseConnector import LabellerDatabaseConnector
from ImageObjectDatabaseConnector import ImageObjectDatabaseConnector
from ObjectExtractionService import ObjectExtractionService

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
        
    
    def get_objects(self, project_id, label):
        query = "SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"
        projects = self.project_db.get_projects(query)




