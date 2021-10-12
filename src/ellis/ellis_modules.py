"""
This module manages the API and the general
design for all Ellis Modules.
"""

# pylint: disable=cyclic-import
# The import being cylcical isn't bad here.

import threading
import logging
from typing import Optional

log = logging.getLogger(__name__)


class EllisModule:
    """
    The base module all Ellis Modules should inherit from.

    ...

    Attributes
    ----------
    running : bool
        Whether or not the module is running
    """
    running = False
    module_name: str = ""

    def __init_subclass__(cls, module_name: Optional[str] = None,
                          *args, **kwargs):
        # pylint: disable=keyword-arg-before-vararg
        super().__init_subclass__(*args, **kwargs)  # type: ignore
        if module_name is None:
            module_name = cls.__name__

        cls.module_name = module_name  # type: ignore
        _Ellis_Registry.register_module(cls, module_name)

    def access_Ellis(self):  # pylint: disable=invalid-name,
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


class _Ellis_Registry:  # pylint: disable=invalid-name
    # pylint: disable=missing-function-docstring
    active_modules: dict[str, EllisModule] = {}
    known_modules: dict[str, type[EllisModule]] = {}
    __instance = None

    @classmethod
    def _add_Ellis(cls, ellis_instance):
        @classmethod
        def dork(cls, ellis):  # pylint: disable=unused-argument
            pass
        cls.__instance = ellis_instance
        cls._add_Ellis = dork  # type: ignore

    @classmethod
    def request_Ellis(cls):
        return cls.__instance

    @classmethod
    def start(cls) -> list[threading.Thread]:
        threads = []
        for (_, module) in cls.known_modules.items():
            threads.append(cls.start_module(module))
            threads[-1].start()
        return threads

    @classmethod
    def stop(cls):
        for (_, module) in cls.active_modules.items():
            cls.stop_module(module, preserve=True)
        cls.active_modules = []

    @classmethod
    def start_module(cls, module: type[EllisModule]) -> threading.Thread:
        def access(self, *args, **kwargs):  # pylint: disable=unused-argument
            return cls.request_Ellis()
        a = module()
        cls.active_modules[module.module_name] = a
        a.access_Ellis = access  # type: ignore
        return threading.Thread(target=a.start, name=module.module_name)

    @classmethod
    def stop_module(cls, module, preserve=False):
        cls.active_modules[module.module_name].stop()
        if not preserve:
            del cls.active_modules[module.module_name]

    @classmethod
    def register_module(cls, module: type[EllisModule], module_name: str):
        cls.known_modules[module_name] = module


from ellis import load_modules  # pylint: disable=wrong-import-position, unused-import # noqa: F401, E501, E402
