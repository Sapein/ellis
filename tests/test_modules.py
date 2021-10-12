""" This file exists to test modules api. """
# pylint: disable=protected-access, abstract-method

from ellis import ellis_modules


TEST_MODULE_NAME = "Test"


class TestModule(ellis_modules.EllisModule):
    """
    This is just a fake-module.


    See Also
    ---------
    ellis.ellis_module
    """

    def start(self, *args, **kwargs) -> tuple[str, bool]:
        """ Starts the module. """
        self.running = True
        return self.module_name, self.running

    def stop(self, *args, **kwargs) -> bool:
        """ Stops the module. """
        self.running = False
        return self.running


class TestModuleName(TestModule, module_name=TEST_MODULE_NAME):
    """
    This is just a fake module

    See Also
    --------
    ellis.ellis_module
    """


class TestModules:
    # pylint: disable=no-self-use
    """ This test exists mostly to test the module API itself. """

    def test_names(self):
        """ Tests the setting of names for modules. """
        assert TestModule.module_name == "TestModule"
        assert TestModuleName.module_name == TEST_MODULE_NAME

    def test_start(self):
        """ Tests and ensures that calling start on the modules works. """
        assert TestModule().start() == (TestModule.module_name, True)
        assert TestModuleName().start() == (TEST_MODULE_NAME, True)

    def test_stop(self):
        """ Tests and ensures that calling start on the modules works. """
        _a = TestModule()
        _b = TestModuleName()
        _a.start()
        _b.start()
        assert _a.stop() is False
        assert _b.stop() is False


class TestRegistry():
    # pylint: disable=no-self-use
    """ This class tests the registry itself. """

    def test_registry_detection(self):
        """ Tests the registry's ability to find modules. """
        known_modules = ellis_modules._Ellis_Registry.known_modules
        active_modules = ellis_modules._Ellis_Registry.active_modules
        assert known_modules[TestModule.module_name] == TestModule
        assert known_modules["Test"] == TestModuleName
        assert active_modules == {}

    def test_register_module(self):
        """ Tests the ability of the registry to register modules. """
        ellis_modules._Ellis_Registry.register_module("random", "MyName")
        module = ellis_modules._Ellis_Registry.known_modules["MyName"]
        assert module == "random"
        del ellis_modules._Ellis_Registry.known_modules["MyName"]

    def test_start_module(self):
        """ Tests the ability of the registry to start a module. """
        thread = ellis_modules._Ellis_Registry.start_module(TestModule)
        assert thread.is_alive() is False

    def test_stop_module(self):
        """ Tests the ability of the registry to stop a module. """
        ellis_modules._Ellis_Registry.stop_module(TestModule)

    def test_request_ellis(self):
        """ Tests the ability of the registry to return ellis. """
        assert ellis_modules._Ellis_Registry.request_Ellis() is None

    def test_start(self):
        """ Tests the ability of the registry to start modules. """
        del ellis_modules._Ellis_Registry.known_modules["Autorecruit"]
        threads = ellis_modules._Ellis_Registry.start()
        assert isinstance(threads, list)
        assert len(threads) == 2
        assert len(ellis_modules._Ellis_Registry.active_modules) == 2

    def test_stop(self):
        """ Tests the ability of the registry to stop modules."""
        ellis_modules._Ellis_Registry.stop()
        assert len(ellis_modules._Ellis_Registry.active_modules) == 0
