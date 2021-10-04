"""
This module manages the API and the general
design for all Ellis Modules.
"""

import threading
import logging
from typing import Optional

log = logging.getLogger(__name__)

class Ellis_Module:
    """
    The base module all Ellis Modules should inherit from.

    ...

    Attributes
    ----------
    running : bool
        Whether or not the module is running
    """
    running = False

    def __init_subclass__(cls, /, module_name: Optional[str]=None, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if module_name is None:
            module_name = cls.__name__

        cls.module_name = module_name
        _Ellis_Registry.register_module(cls, module_name)

    def access_Ellis(self):
        """
        Returns the instance of Ellis, if provided to the Module.

        This returns the instance of Ellis currently being ran, if the
        Registry has decided to make it available to the module.

        Returns
        -------
        EllisServer
            Returns the currently running Ellis Instance.

        Raises
        ------
        NotImplementedError
            If the Registry has not provided access to the Module.

        Notes
        -----
        This module is provided only to provide access to Ellis
        directly if the module needs it, but otherwise this method
        should *NOT* be called, nor should the intstance be stored.

        The client should *NOT* override this method.
        """
        raise NotImplementedError

    def start(self, *args, **kwargs):
        """
        Starts the Module up and begins running.

        Notes
        -----
        This method should never be directly called, It is
        automatically called by Ellis once the module system
        is started. This should set running to True.
        """
        raise NotImplementedError

    def stop(self, *args, **kwargs):
        """
        Stops the module and should shut down the module.

        Notes
        -----
        This method shouldn't really be called, but may be
        called in any case to ensure that the Module is shutdown
        cleanly. The module should assume the server is going down,
        but it is not necessary.
        """
        raise NotImplementedError

class _Ellis_Registry:
    active_modules: dict[str, Ellis_Module] = {}
    known_modules: dict[str, type[Ellis_Module]] = {}
    __instance = None

    @classmethod
    def _add_Ellis(cls, ellis_instance):
        @classmethod
        def l(cls, ellis):
            pass
        cls.__instance = ellis_instance
        cls._add_Ellis = l

    @classmethod
    def request_Ellis(cls):
        return cls.__instance

    @classmethod
    def start(cls):
        threads = []
        for module in cls.known_modules:
            threads.append(cls.start_module(cls.known_modules[module]))
            threads[-1].start()
        return threads

    @classmethod
    def stop(cls):
        for module in cls.known_modules:
            cls.stop_module(cls.known_modules[module])

    @classmethod
    def start_module(cls, module) -> threading.Thread:
        def access(self, *args, **kwargs):
            return cls.request_Ellis()
        a = module()
        cls.active_modules[module.module_name] = a
        a.access_Ellis = access
        return threading.Thread(target=a.start, name=module.module_name)

    @classmethod
    def stop_module(cls, module):
        cls.active_modules[module.module_name].stop()
        del cls.active_modules[module.module_name]

    @classmethod
    def register_module(cls, module: type[Ellis_Module], module_name: str):
        cls.known_modules[module_name] = module

import load_modules
