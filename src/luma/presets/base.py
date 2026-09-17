class BasePreset:
    """
    Base class for all Luma presets.

    Individual presets inherit from this class and provide their
    own name, category, description and image-processing settings.

    Keeping this shared structure makes it easier to add and organise
    a large number of presets as Luma grows.
    """

    name = "base"

    category = "Other"

    description = "Base Luma preset"

    settings = {}