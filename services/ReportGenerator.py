from ProjectDatabaseConnector import ProjectDatabaseConnector, MYSQLProjectDatabaseConnector
from LabelDatabaseConnector import LabelDatabaseConnector, MYSQLLabelDatabaseConnector
from LabellerDatabaseConnector import LabellerDatabaseConnector, MYSQLLabellerDatabaseConnector
from ImageObjectDatabaseConnector import ImageObjectDatabaseConnector, MYSQLImageObjectDatabaseConnector
from ObjectExtractionService import ObjectExtractionService
from ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector


class ReportGenerator():

    def __init__(self):
        self.ProjectDatabaseConnector = MYSQLProjectDatabaseConnector()
        self.LabelDatabaseConnector = MYSQLLabelDatabaseConnector()
        self.ImageObjectDatabaseConnector = MYSQLImageObjectDatabaseConnector()
        self.LabellerDatabaseConnector = MYSQLLabellerDatabaseConnector()
        self.ICMDB = MYSQLImageClassMeasureDatabaseConnector()

    def get_report_info(self, project_id) -> dict:
        query_projects = f"SELECT * FROM my_image_db.Projects WHERE projectId = {project_id};"
        project = self.ProjectDatabaseConnector.get_projects(query_projects)[0]

        for image in project.images:
            query_labels = f"SELECT * FROM my_image_db.Labels WHERE (OrigImageID = {image.ImageID});"
            labels = self.LabelDatabaseConnector.get_labels(query_labels)
            print(f"found {len(labels)} labels")
            labeller_ids = set()
            for label in labels:
                labeller_ids.add(label.LabellerID)

            query_labellers = f"SELECT * FROM my_image_db.Labeller_skills WHERE Labeller_id IN :ids"

            labellers = self.LabellerDatabaseConnector.get_labellers_with_data(query_labellers, {'ids': tuple(labeller_ids)})
            
            print(labellers)
            print(labels[0].__dict__)


r = ReportGenerator()
r.get_report_info(14)

