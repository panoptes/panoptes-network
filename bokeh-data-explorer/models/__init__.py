from panoptes.utils.library import load_module


class Model():
    """Model Factory"""

    @classmethod
    def get_model(cls, model_name, *args, **kwargs):
        model_class = load_module(f'models.{model_name}')
        model = model_class.Model(model_name, *args, **kwargs)

        return model
