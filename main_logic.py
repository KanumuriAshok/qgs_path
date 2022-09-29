"""
Model exported as python.
Name : demand_cluster
Group : 
With QGIS : 32003
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsExpression
import processing


class Demand_cluster(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('demandpoints', 'demand points', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('street', 'street', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('StreetBuffer', 'street buffer', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, supportsAppend=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('HubLines', 'hub lines', type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Clustered', 'clustered', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Meanpoints', 'meanpoints', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # Variable width buffer (by M value)
        alg_params = {
            'INPUT': parameters['street'],
            'SEGMENTS': 2,
            'OUTPUT': parameters['StreetBuffer']
        }
        outputs['VariableWidthBufferByMValue'] = processing.run('native:bufferbym', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['StreetBuffer'] = outputs['VariableWidthBufferByMValue']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # K-means clustering
        alg_params = {
            'CLUSTERS': 2,
            'FIELD_NAME': 'CLUSTER_ID',
            'INPUT': parameters['demandpoints'],
            'SIZE_FIELD_NAME': '24',
            'OUTPUT': parameters['Clustered']
        }
        outputs['KmeansClustering'] = processing.run('native:kmeansclustering', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Clustered'] = outputs['KmeansClustering']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Mean coordinate(s)
        alg_params = {
            'INPUT': outputs['KmeansClustering']['OUTPUT'],
            'UID': '',
            'WEIGHT': QgsExpression('').evaluate(),
            'OUTPUT': parameters['Meanpoints']
        }
        outputs['MeanCoordinates'] = processing.run('native:meancoordinates', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Meanpoints'] = outputs['MeanCoordinates']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Join by lines (hub lines)
        alg_params = {
            'ANTIMERIDIAN_SPLIT': False,
            'GEODESIC': True,
            'GEODESIC_DISTANCE': 1000,
            'HUBS': outputs['MeanCoordinates']['OUTPUT'],
            'HUB_FIELD': '1',
            'HUB_FIELDS': [''],
            'SPOKES': outputs['KmeansClustering']['OUTPUT'],
            'SPOKE_FIELD': 'cluster_id',
            'SPOKE_FIELDS': [''],
            'OUTPUT': parameters['HubLines']
        }
        outputs['JoinByLinesHubLines'] = processing.run('native:hublines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['HubLines'] = outputs['JoinByLinesHubLines']['OUTPUT']
        return results

    def name(self):
        return 'demand_cluster1'

    def displayName(self):
        return 'demand_cluster1'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Demand_cluster()
