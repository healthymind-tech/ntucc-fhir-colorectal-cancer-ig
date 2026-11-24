import pytest

from reference.icdo3 import morphology, topography


@pytest.mark.parametrize("raw, expected", [("C187", "C18.7"), ("C18.7", "C18.7"), ("c187", "C18.7"), (" C209 ", "C20.9"), ("C180", "C18.0")])
def test_topography(raw, expected):
    assert topography(raw) == expected


@pytest.mark.parametrize("raw", ["C18", "C18.70", "C1877", "1234", "CXX9", "D125", "", "C18-7"])
def test_topography_rejects_malformed(raw):
    with pytest.raises(ValueError):
        topography(raw)


@pytest.mark.parametrize("histology, behavior, expected", [("8140", "3", "8140/3"), ("8936", "1", "8936/1"), (" 8148 ", "2", "8148/2"), ("8240", "3", "8240/3")])
def test_morphology(histology, behavior, expected):
    assert morphology(histology, behavior) == expected


@pytest.mark.parametrize("histology, behavior", [("814", "3"), ("81400", "3"), ("8140", "33"), ("8140", "4"), ("8140", ""), ("abcd", "3")])
def test_morphology_rejects_malformed(histology, behavior):
    with pytest.raises(ValueError):
        morphology(histology, behavior)
