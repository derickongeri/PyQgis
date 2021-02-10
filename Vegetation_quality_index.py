"""
Model exported as python.
Name : Vegetation Quality Index
Group : 
With QGIS : 31603
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
import processing


class VegetationQualityIndex(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterRasterLayer('ESACCILandCover', 'ESA_CCI_LandCover', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('PlantCoverMaxNDVIComposite', 'Plant_Cover(MaxNDVI Composite)', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('ErosionProtectionIndex', 'Erosion Protection Index', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('FireRisckScore', 'Fire Risck score', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('DroughtResistanceScore', 'Drought Resistance Score', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('Plant_cover_score', 'Plant_Cover_Score', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('VegetationQualityIndex', 'Vegetation Quality Index', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}

        # plant cover
        alg_params = {
            'CELLSIZE': 0,
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'EXPRESSION': ' ( \"Plant_Cover(MaxNDVI Composite)@1\" * 0.92 )  / 250',
            'EXTENT': None,
            'LAYERS': parameters['PlantCoverMaxNDVIComposite'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PlantCover'] = processing.run('qgis:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # r.reclass(fire risk)
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': parameters['ESACCILandCover'],
            'rules': '',
            'txtrules': '140 160 200 201 202 = 1\n90 170 180 = 2\n12 72 151 152 = 3\n153 150 130 82 81 80 71 61 50 = 4\n10 11 20 40 60 110 120 122 = 5\n100 70 30 = 6\n121 = 7\n62 = 8',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RreclassfireRisk'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # r.reclass(Erosion)
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': parameters['ESACCILandCover'],
            'rules': '',
            'txtrules': '50 61 71 90 160 = 1\n60 70 140 = 2\n100 121 170 180 = 3\n72 80 110 = 4\n20 40 62 130 = 5\n30 81 82 = 6\n12 120 151 152 = 7\n10 150 153 = 8\n11 = 9\n200 201 202 = 10',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rreclasserosion'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # plant cover score
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['PlantCover']['OUTPUT'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': 0,
            'RANGE_BOUNDARIES': 0,
            'RASTER_BAND': 1,
            'TABLE': [0,0.1,2.0,0.1,0.11,1.9,0.11,0.13,1.8,0.13,0.18,1.7,0.18,0.26,1.6,0.26,0.38,1.5,0.38,0.50,1.4,0.50,0.62,1.3,0.62,0.72,1.2,0.72,0.80,1.1,0.8,0.92,1.0],
            'OUTPUT': parameters['Plant_cover_score']
        }
        outputs['PlantCoverScore'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Plant_cover_score'] = outputs['PlantCoverScore']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Erosion risk
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['Rreclasserosion']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': 0,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [1,2,1.0,2,3,1.1,3,4,1.2,4,5,1.3,5,6,1.4,6,7,1.5,7,8,1.6,8,9,1.7,9,10,1.8,10,11,2.0],
            'OUTPUT': parameters['ErosionProtectionIndex']
        }
        outputs['ErosionRisk'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ErosionProtectionIndex'] = outputs['ErosionRisk']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # r.reclass(Drought resistance)
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': parameters['ESACCILandCover'],
            'rules': '',
            'txtrules': '170 160 140 90 61 50 = 1\n180 71 70 60 = 2\n121 80 72 62 = 3\n110 82 81 12 = 4\n122 100 20 = 5\n152 151 120 40 30 10 = 6\n153 150 130 11 = 7\n200 201 202 = 8',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RreclassdroughtResistance'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Fire risk
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['RreclassfireRisk']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': 0,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [1,2,1.0,2,3,1.1,3,4,1.2,4,5,1.3,5,6,1.4,6,7,1.5,7,8,1.6,8,9,1.7],
            'OUTPUT': parameters['FireRisckScore']
        }
        outputs['FireRisk'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['FireRisckScore'] = outputs['FireRisk']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Drought resistance
        alg_params = {
            'DATA_TYPE': 5,
            'INPUT_RASTER': outputs['RreclassdroughtResistance']['output'],
            'NODATA_FOR_MISSING': True,
            'NO_DATA': 0,
            'RANGE_BOUNDARIES': 1,
            'RASTER_BAND': 1,
            'TABLE': [1,2,1.0,2,3,1.1,3,4,1.2,4,5,1.3,5,6,1.4,6,7,1.5,7,8,1.6,8,9,2.0],
            'OUTPUT': parameters['DroughtResistanceScore']
        }
        outputs['DroughtResistance'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['DroughtResistanceScore'] = outputs['DroughtResistance']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # VQI calculation
        alg_params = {
            'CELLSIZE': 0,
            'CRS': QgsCoordinateReferenceSystem('EPSG:4326'),
            'EXPRESSION': ' ( \"\'Plant_Cover_Score\' from algorithm \'plant cover score\'@1\" * \"\'Drought Resistance Score\' from algorithm \'Drought resistance\'@1\" * \"\'Fire Risck score\' from algorithm \'Fire risk\'@1\" * \"\'Erosion Protection Index\' from algorithm \'Erosion risk\'@1\" )  ^  ( 1/4 ) ',
            'EXTENT': None,
            'LAYERS': outputs['FireRisk']['OUTPUT'],
            'OUTPUT': parameters['VegetationQualityIndex']
        }
        outputs['VqiCalculation'] = processing.run('qgis:rastercalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['VegetationQualityIndex'] = outputs['VqiCalculation']['OUTPUT']
        return results

    def name(self):
        return 'Vegetation Quality Index'

    def displayName(self):
        return 'Vegetation Quality Index'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return VegetationQualityIndex()
