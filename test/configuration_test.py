import pytest
from configuration import Configuration, ConfigurationException

def test_config_validation():

    config = Configuration("test/config/template.toml")
    assert config.validate()

def test_config_validation_invalid_field():
    config = Configuration("test/config/invalid_field.toml")
    with pytest.raises(ConfigurationException):
        config.validate()

def test_config_file_not_found():
    config = Configuration("test/config/aaaa.toml")
    with pytest.raises(ConfigurationException):
        config.read()