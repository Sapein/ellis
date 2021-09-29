"""
This is the Ellis Module API, and is mostly so that we can move things outside of
the main Ellis module...
"""

import threading
import logging
from typing import Optional

class Ellis_Module:
    running = False
    def __init_subclass__(cls, /, module_name: Optional[str]=None, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        if module_name is None:
            module_name = cls.__name__

        cls.module_name = module_name
        _Ellis_Registry.register_module(cls, module_name)

    def access_Ellis(self, *args, **kwargs):
        """ Do not override. """
        raise NotImplementedError

    def start(self, *args, **kwargs):
        raise NotImplementedError

    def stop(self, *args, **kwargs):
        raise NotImplementedError

class _Ellis_Registry:
    active_modules = {}
    known_modules = {}
    __instance = None

    @classmethod
    def request_Ellis(cls):
        return cls.__instance

    @classmethod
    def _add_Ellis(cls, ellis_instance):
        @classmethod
        def l(cls, ellis):
            pass
        cls.__instance = ellis_instance
        cls._add_Ellis = l

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
        return threading.Thread(target=a.start)

    @classmethod
    def stop_module(cls, module):
        cls.active_modules[module.module_name].stop()
        del cls.active_modules[module.module_name]

    @classmethod
    def register_module(cls, module: Ellis_Module, module_name: str):
        cls.known_modules[module_name] = module

import load_modules
