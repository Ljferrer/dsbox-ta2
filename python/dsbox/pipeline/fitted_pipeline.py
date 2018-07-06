import os
import json
import pickle
import typing
import uuid

from networkx import nx

from d3m.container.dataset import Dataset
from d3m.metadata.pipeline import Pipeline, StepBase

from dsbox.template.runtime import Runtime
# from dsbox.template.search import ConfigurationSpace, ConfigurationPoint
from dsbox.template.template import to_digraph, DSBoxTemplate
import pprint

import typing
# python path of primitive, i.e. 'd3m.primitives.common_primitives.RandomForestClassifier'
PythonPath = typing.NewType('PythonPath', str)
TP = typing.TypeVar('TP', bound='FittedPipeline')

class FittedPipeline:
    """
    Fitted pipeline
    Attributes
    ----------
    pipeline: Pipeline
        a pipeline
    dataset: Dataset
        identifier for a dataset
    runtime: Runtime
        runtime object for the pipeline
    id: str
        the id of the pipeline
    folder_loc: str
        the location of the files of pipeline
    """

    def __init__(self,
                 pipeline: Pipeline,
                 dataset_id: str = None, id: str = None) -> None:

        # these two are mandatory
        # TODO add the check
        self.dataset_id = dataset_id
        self.pipeline = pipeline

        if id is None:
            # Create id distinct, since there may be several fitted pipelines
            #  using the same pipeline
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        # self.folder_loc = ''

        self.runtime = Runtime(pipeline)

    def _set_fitted(self, fitted_pipe: typing.List[StepBase]) -> None:
        self.runtime.pipeline = fitted_pipe

    # @classmethod
    # def create(cls: typing.Type[TP],
    #            configuration:ConfigurationPoint,
    #            dataset: Dataset) -> TP:
    #     '''
    #     Initialize the FittedPipeline with the configurations
    #     '''
    #
    #     assert False, "This method is deprecated!"
    #
    #     # pipeline_to_load = template.to_pipeline(configuration)
    #     # run = []#configuration.data['runtime']
    #     fitted_pipe = configuration.data['fitted_pipe']
    #     pipeline = configuration.data['pipeline']
    #     exec_order = configuration.data['exec_plan']
    #
    #
    #     fitted_pipeline_loaded = cls(
    #         fitted_pipe=fitted_pipe,
    #         pipeline=pipeline,
    #         exec_order=exec_order,
    #         dataset_id=dataset.metadata.query(())['id']
    #     )
    #     return fitted_pipeline_loaded

    def fit(self, **arguments):
        self.runtime.fit(**arguments)

    def produce(self, **arguments):
        self.runtime.produce(**arguments)

    def get_fit_step_output(self, step_number: int):
        return self.runtime.fit_outputs[step_number]

    def get_produce_step_output(self, step_number: int):
        return self.runtime.produce_outputs[step_number]


    def save(self, folder_loc : str) -> None:
        '''
        Save the given fitted pipeline from TemplateDimensionalSearch
        '''
        self.folder_loc = folder_loc
        # print("The pipeline files will be stored in:")
        # print(self.folder_loc)

        pipeline_dir = os.path.join(self.folder_loc, 'pipelines')
        executable_dir = os.path.join(self.folder_loc, 'executables', self.id)
        os.makedirs(pipeline_dir, exist_ok=True)
        os.makedirs(executable_dir, exist_ok=True)

        # print("Writing:",self)
        # # save the pipeline with json format
        # json_loc = os.path.join(pipeline_dir, self.id + '.json')
        # with open(json_loc, 'w') as f:
        #     self.pipeline.to_json(f)

        # store fitted_pipeline id
        structure = self.pipeline.to_json_structure()
        structure['fitted_pipeline_id'] = self.id
        structure['dataset_id'] = self.dataset_id

        # save the pipeline with json format
        json_loc = os.path.join(pipeline_dir, self.id + '.json')
        with open(json_loc, 'w') as out:
            json.dump(structure, out)



        # save the pickle files of each primitive step
        for i in range(0, len(self.runtime.execution_order)):
            # print("Now saving step_", i)
            n_step = self.runtime.execution_order[i]
            each_step = self.runtime.pipeline[n_step]
            '''
            NOTICE:
            running both of get_params and hyperparams will cause the error of
            "AttributeError: 'RandomForestClassifier' object has no attribute 'oob_score_'"
            print(each_primitive.get_params())
            print(each_step.hyperparams)
            '''
            file_loc = os.path.join(executable_dir, "step_" + str(i) + ".pkl")

            with open(file_loc, "wb") as f:
                pickle.dump(each_step, f)

    def __str__(self):
        # desc = list(map(lambda s: (s.primitive, s.hyperparams),
        #                 ))
        return pprint.pformat(self.runtime.pipeline)
        # print("Sorted:", dag_order)
        # return str(dag_order)

    @classmethod
    def load(cls:typing.Type[TP], folder_loc: str,
             pipeline_id: str, dataset_id: str = None) -> TP:
        '''
        Load the pipeline with given pipeline id and folder location
        '''
        # load pipeline from json
        pipeline_dir = os.path.join(folder_loc, 'pipelines')
        executable_dir = os.path.join(folder_loc, 'executables', pipeline_id)

        # json_loc = os.path.join(pipeline_dir, pipeline_id + '.json')
        # print("The following pipeline file will be loaded:")
        # print(json_loc)
        # with open(json_loc, 'r') as f:
        #     pipeline_to_load = Pipeline.from_json(f)

        json_loc = os.path.join(pipeline_dir, pipeline_id + '.json')
        print("The following pipeline file will be loaded:")
        print(json_loc)
        with open(json_loc, 'r') as f:
            structure = json.load(f)

        fitted_pipeline_id = structure['fitted_pipeline_id']
        dataset_id = structure['dataset_id']

        pipeline_to_load = Pipeline.from_json_structure(structure)

        # load detail fitted parameters from pkl files
        run = Runtime(pipeline_to_load)

        for i in range(0, len(run.execution_order)):
            n_step = run.execution_order[i]
            file_loc = os.path.join(executable_dir, "step_" + str(i) + ".pkl")
            with open(file_loc, "rb") as f:
                each_step = pickle.load(f)
                run.pipeline[n_step] = each_step


        # fitted_pipeline_loaded = cls(pipeline_to_load, run, dataset)
        fitted_pipeline_loaded = cls(pipeline=pipeline_to_load,
                                     dataset_id=dataset_id,
                                     id=fitted_pipeline_id)
        fitted_pipeline_loaded._set_fitted(run.pipeline)

        return (fitted_pipeline_loaded, run)

    def __getstate__(self) -> typing.Dict:
        """
        This method is used by the pickler as the state of object.
        The object can be recovered through this state uniquely.

        Returns:
            state: Dict
                dictionary of important attributes of the object

        """
        # print("[INFO] Get state called")

        state = self.__dict__  # get attribute dictionary

        # add the fitted_primitives
        state['fitted_pipe'] = self.runtime.pipeline
        state['pipeline'] = self.pipeline.to_json_structure()
        del state['runtime']  # remove runtime entry

        return state

    def __setstate__(self, state: typing.Dict) -> None:
        """
        This method is used for unpickling the object. It takes a dictionary
        of saved state of object and restores the object to that state.
        Args:
            state: typing.Dict
                dictionary of the objects picklable state
        Returns:

        """

        # print("[INFO] Set state called!")

        fitted = state['fitted_pipe']
        del state['fitted_pipe']

        structure = state['pipeline']
        state['pipeline'] = Pipeline.from_json_structure(structure)

        run = Runtime(state['pipeline'])
        run.pipeline = fitted

        state['runtime'] = run

        self.__dict__ = state
