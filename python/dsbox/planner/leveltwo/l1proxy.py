from dsbox.planner.levelone.planner import (LevelOnePlanner, get_d3m_primitives, AffinityPolicy)
from dsbox.planner.leveltwo.primitives.library import PrimitiveLibrary
from dsbox.schema.dataset_schema import VariableFileType

class LevelOnePlannerProxy(object):
    """
    The Level-1 DSBox Proxy Planner.

    This is here to integrate with Ke-Thia's L1 Planner until we come up with a consistent interface
    """
    def __init__(self, libdir, task_type, task_subtype, media_type=None):
        self.models = PrimitiveLibrary(libdir+"/models.json")
        self.features = PrimitiveLibrary(libdir+"/features.json")

        self.primitives = get_d3m_primitives()
        self.policy = AffinityPolicy(self.primitives)
        self.media_type = media_type
        self.l1_planner = LevelOnePlanner(primitives=self.primitives, policy=self.policy,
                task_type=task_type, task_subtype=task_subtype, media_type=self.media_type)

        self.primitive_hash = {}
        for model in self.models.primitives:
            self.primitive_hash[model.name] = model
        for feature in self.features.primitives:
            self.primitive_hash[feature.name] = feature

        self.pipeline_hash = {}

    def get_pipelines(self, data):
        l1_pipelines = self.l1_planner.generate_pipelines_with_hierarchy(level=2)

        # If there is a media type, use featurisation-added pipes instead
        # kyao: added check to skip if media_type is nested tables
        if self.media_type and not self.media_type==VariableFileType.TABULAR:
            new_pipes = []
            for l1_pipeline in l1_pipelines:
                refined_pipes = self.l1_planner.fill_feature_by_weights(l1_pipeline, 1)
                new_pipes = new_pipes + refined_pipes
            l1_pipelines = new_pipes

        pipelines = []
        for l1_pipeline in l1_pipelines:
            pipeline = self.l1_to_proxy_pipeline(l1_pipeline)
            if pipeline:
                self.pipeline_hash[str(pipeline)] = l1_pipeline
                pipelines.append(pipeline)
        return pipelines

    def l1_to_proxy_pipeline(self, l1_pipeline):
        pipeline = []
        ok = True
        for prim in l1_pipeline.get_primitives():
            l2prim = self.primitive_hash.get(prim.name, None)
            if not l2prim:
                ok = False
                break
            pipeline.append(l2prim)

        if ok:
            return pipeline
        return None

    def get_related_pipelines(self, pipeline):
        pipelines = []
        l1_pipeline = self.pipeline_hash.get(str(pipeline), None)
        if l1_pipeline:
            l1_pipelines = self.l1_planner.find_similar_learner(l1_pipeline, include_siblings=True)
            for l1_pipeline in l1_pipelines:
                pipeline = self.l1_to_proxy_pipeline(l1_pipeline)
                if pipeline:
                    self.pipeline_hash[str(pipeline)] = l1_pipeline
                    pipelines.append(pipeline)
        return pipelines
