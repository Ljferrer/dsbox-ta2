import typing

from enum import Enum

from d3m import utils, index
from d3m.container.dataset import Dataset
from d3m.metadata.pipeline import PrimitiveStep,  ArgumentType
from d3m.metadata.problem import TaskType, TaskSubtype

from dsbox.template.template import TemplatePipeline, TemplateStep, SemanticType


class TemplateDescription:
    """
    Description of templates in the template library.

    Attributes
    ----------
    task : TaskType
        The type task the template handles
    template: TemplatePipeline
        The actual template
    target_step: int
        The step of the template that extract the ground truth target from the dataset
    predicted_target_step: int
        The step of the template generates the predictions
    """
    def __init__(self, task: TaskType, template: TemplatePipeline, target_step: int, predicted_target_step: int) -> None:
        self.task = task
        self.template = template

        # Instead of having these attributes here, probably should attach attributes to the template steps
        self.target_step = target_step
        self.predicted_target_step = predicted_target_step

class TemplateLibrary:
    """
    Library of template pipelines
    """

    def __init__(self, library_dir: str = None) -> None:
        self.templates: typing.List[TemplateDescription] = []
        self.primitive: typing.Dict = index.search()

        self.library_dir = library_dir
        if self.library_dir is None:
            self._load_library()

        self._load_inline_templates()

    def get_templates(self, task: TaskType, subtype: TaskSubtype) -> typing.List[TemplateDescription]:
        results = []
        for desc in self.templates:
            if desc.task == task:
                results.append(desc)
        return results

    def _load_library(self):
        # TODO
        #os.path.join(library_dir, 'template_library.yaml')
        pass

    def _load_inline_templates(self):
        self.templates.append(self._generate_simple_classifer_template())
        self.templates.append(self._generate_simple_regressor_template())

    def _generate_simple_classifer_template(self) -> TemplateDescription:
        """
        Default classification template
        """
        template = TemplatePipeline(context='PRETRAINING')

        denormalize_step = PrimitiveStep(self.primitive['d3m.primitives.datasets.Denormalize'].metadata.query())
        to_DataFrame_step = PrimitiveStep(self.primitive['d3m.primitives.datasets.DatasetToDataFrame'].metadata.query())
        column_parser_step = PrimitiveStep(self.primitive['d3m.primitives.data.ColumnParser'].metadata.query())
        extract_attribute_step = PrimitiveStep(self.primitive['d3m.primitives.data.ExtractAttributes'].metadata.query())
        cast_1_step = PrimitiveStep(self.primitive['d3m.primitives.data.CastToType'].metadata.query())
        impute_step = PrimitiveStep(self.primitive['d3m.primitives.sklearn_wrap.SKImputer'].metadata.query())
        extract_target_step = PrimitiveStep(self.primitive['d3m.primitives.data.ExtractTargets'].metadata.query())
        cast_2_step = PrimitiveStep(self.primitive['d3m.primitives.data.CastToType'].metadata.query())

        model_step = TemplateStep('modeller', SemanticType.CLASSIFIER)

        template_input = template.add_input('input dataset')

        template.add_step(denormalize_step)
        template.add_step(to_DataFrame_step)
        template.add_step(column_parser_step)
        template.add_step(extract_attribute_step)
        template.add_step(cast_1_step)
        template.add_step(impute_step)
        template.add_step(extract_target_step)
        template.add_step(cast_2_step)

        template.add_step(model_step)
        # template.add_step(prediction_step)

        denormalize_step.add_argument('inputs',  ArgumentType.CONTAINER, template_input)
        denormalize_step_produce = denormalize_step.add_output('produce')

        to_DataFrame_step.add_argument('inputs', ArgumentType.CONTAINER, denormalize_step_produce)
        to_DataFrame_produce = to_DataFrame_step.add_output('produce')

        column_parser_step.add_argument('inputs', ArgumentType.CONTAINER, to_DataFrame_produce)
        column_parser_produce = column_parser_step.add_output('produce')

        extract_attribute_step.add_argument('inputs', ArgumentType.CONTAINER, column_parser_produce)
        extract_attribute_produce = extract_attribute_step.add_output('produce')

        cast_1_step.add_argument('inputs', ArgumentType.CONTAINER, extract_attribute_produce)
        cast_1_produce = cast_1_step.add_output('produce')

        impute_step.add_argument('inputs', ArgumentType.CONTAINER, cast_1_produce)
        impute_produce = impute_step.add_output('produce')

        extract_target_step.add_argument('inputs', ArgumentType.CONTAINER, column_parser_produce)
        extract_target_produce = extract_target_step.add_output('produce')

        # Is this step needed?
        cast_2_step.add_argument('inputs', ArgumentType.CONTAINER, extract_target_produce)
        cast_2_produce = cast_2_step.add_output('produce')


        model_step.add_expected_argument('inputs', ArgumentType.CONTAINER)
        model_step.add_expected_argument('outputs', ArgumentType.CONTAINER)
        model_step.add_input(impute_produce)
        model_step.add_input(cast_2_produce)
        model_produce = model_step.add_output('produce')

        template_output = template.add_output(model_produce, 'predictions from the input dataset')

        description = TemplateDescription(TaskType.CLASSIFICATION, template, template.steps.index(extract_target_step),
                                          template.steps.index(model_step))
        return description

    def _generate_simple_regressor_template(self) -> TemplateDescription:
        """
        Default regression template
        """
        template = TemplatePipeline(context='PRETRAINING')

        denormalize_step = PrimitiveStep(self.primitive['d3m.primitives.datasets.Denormalize'].metadata.query())
        to_DataFrame_step = PrimitiveStep(self.primitive['d3m.primitives.datasets.DatasetToDataFrame'].metadata.query())
        column_parser_step = PrimitiveStep(self.primitive['d3m.primitives.data.ColumnParser'].metadata.query())
        extract_attribute_step = PrimitiveStep(self.primitive['d3m.primitives.data.ExtractAttributes'].metadata.query())
        cast_1_step = PrimitiveStep(self.primitive['d3m.primitives.data.CastToType'].metadata.query())
        impute_step = PrimitiveStep(self.primitive['d3m.primitives.sklearn_wrap.SKImputer'].metadata.query())
        extract_target_step = PrimitiveStep(self.primitive['d3m.primitives.data.ExtractTargets'].metadata.query())
        # cast_2_step = PrimitiveStep(self.primitive['d3m.primitives.data.CastToType'].metadata.query())

        model_step = TemplateStep('modeller', SemanticType.REGRESSOR)

        template_input = template.add_input('input dataset')

        template.add_step(denormalize_step)
        template.add_step(to_DataFrame_step)
        template.add_step(column_parser_step)
        template.add_step(extract_attribute_step)
        template.add_step(cast_1_step)
        template.add_step(impute_step)
        template.add_step(extract_target_step)
        # template.add_step(cast_2_step)
        template.add_step(model_step)
        # template.add_step(prediction_step)

        denormalize_step.add_argument('inputs', ArgumentType.CONTAINER, template_input)
        denormalize_step_produce = denormalize_step.add_output('produce')

        to_DataFrame_step.add_argument('inputs', ArgumentType.CONTAINER, denormalize_step_produce)
        to_DataFrame_produce = to_DataFrame_step.add_output('produce')

        column_parser_step.add_argument('inputs', ArgumentType.CONTAINER, to_DataFrame_produce)
        column_parser_produce = column_parser_step.add_output('produce')

        extract_attribute_step.add_argument('inputs', ArgumentType.CONTAINER, column_parser_produce)
        extract_attribute_produce = extract_attribute_step.add_output('produce')

        cast_1_step.add_argument('inputs', ArgumentType.CONTAINER, extract_attribute_produce)
        cast_1_produce = cast_1_step.add_output('produce')

        impute_step.add_argument('inputs', ArgumentType.CONTAINER, cast_1_produce)
        impute_produce = impute_step.add_output('produce')

        extract_target_step.add_argument('inputs', ArgumentType.CONTAINER, column_parser_produce)
        extract_target_produce = extract_target_step.add_output('produce')

        # cast_2_step.add_argument('inputs', ArgumentType.CONTAINER, extract_target_produce)
        # cast_2_produce = cast_2_step.add_output('produce')


        model_step.add_expected_argument('inputs', ArgumentType.CONTAINER)
        model_step.add_expected_argument('outputs', ArgumentType.CONTAINER)
        model_step.add_input(impute_produce)
        # model_step.add_input(cast_2_produce)
        model_step.add_input(extract_target_produce)
        model_produce = model_step.add_output('produce')

        template_output = template.add_output(model_produce, 'predictions from the input dataset')

        description = TemplateDescription(TaskType.REGRESSION, template, template.steps.index(extract_target_step), template.steps.index(model_step))
        return description

        
        