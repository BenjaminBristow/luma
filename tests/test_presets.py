import pytest

from luma.presets import PRESETS


def test_presets_are_registered():
    """
    Every preset should be available through the central PRESETS
    registry used by the command-line interface.
    """

    assert PRESETS


def test_expected_presets_are_registered():
    expected_presets = {
        "cinematic",
        "aurora",
        "retro",
        "old-fashioned",
        "sepia",
        "antique",
        "faded",
        "polaroid",
        "film",
        "70s",
        "80s",
        "90s",
        "forest",
        "overgrown",
        "autumn",
        "golden-hour",
        "moss",
        "earthy",
        "ocean",
        "tropical",
        "storm",
        "mist",
        "fog",
        "overcast",
        "moonlight",
        "twilight",
        "industrial",
        "abandoned",
        "grunge",
        "concrete",
        "urban",
        "noir",
        "thriller",
        "horror",
        "dramatic",
        "dreamy",
        "ethereal",
        "crimson",
        "pastel",
        "monochrome",
        "bleach",
    }

    assert expected_presets.issubset(PRESETS.keys())


def test_every_preset_has_required_attributes():
    """
    Every preset must provide the information required by the CLI
    and preset-management system.
    """

    for preset_class in PRESETS.values():
        preset = preset_class()

        assert preset.name
        assert preset.category
        assert preset.description
        assert isinstance(preset.settings, dict)


def test_preset_names_match_registry():
    """
    The name stored inside each preset should match the name used
    to register it in PRESETS.
    """

    for registered_name, preset_class in PRESETS.items():
        preset = preset_class()

        assert preset.name == registered_name


def test_preset_categories_are_valid():
    expected_categories = {
        "Vintage",
        "Nature",
        "Weather & Atmosphere",
        "Urban",
        "Dark & Cinematic",
        "Artistic",
    }

    for preset_class in PRESETS.values():
        preset = preset_class()

        assert preset.category in expected_categories


@pytest.mark.parametrize(
    "preset_class",
    list(PRESETS.values()),
)
def test_preset_settings_contain_valid_values(preset_class):
    """
    Numeric settings should contain integer or floating-point values.
    Colour grading is allowed to contain its own dictionary of values.
    """

    preset = preset_class()

    for setting_name, value in preset.settings.items():

        if setting_name == "colour_grading":
            assert isinstance(value, dict)

            for colour, amount in value.items():
                assert isinstance(colour, str)
                assert isinstance(amount, (int, float))

        else:
            assert isinstance(value, (int, float))