from script_maker.configuration import Configuration


def test_configuration_empty() -> None:
    Configuration.from_runnable_config({})
