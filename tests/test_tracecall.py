""" This tests tracecall """

import pytest
import logging
from ellis.tracecall import tracecall


def return_1():
    return 1
def return_a(a):
    return a
def return_kwarg(b, /, a):
    return a
def return_multiple(a, b):
    return a, b, 3
def return_optkwarg(a=2):
    return a

class A:
    log = logging

    @tracecall()
    def return_1(self):
        return 1

    @tracecall()
    def return_a(self, a):
        return a

    @tracecall()
    def return_kwarg(self, b, /, a):
        return a

    @tracecall()
    def return_multiple(self, a, b):
        return a, b, 3

    @tracecall()
    def return_optkwarg(self, a=2):
        return a


@pytest.fixture()
def log_to_print(monkeypatch):
    monkeypatch.setattr('logging.Logger.debug', print)
    yield
    monkeypatch.undo()

@pytest.mark.parametrize('test_input, expected',
                        [(lambda : return_1(), 1),
                         (lambda : return_a(1), 1),
                         (lambda : return_kwarg(2, a=1), 1),
                         (lambda : return_multiple(1, 2), (1, 2, 3)),
                         (lambda : return_optkwarg(1), 1),
                         (lambda : return_optkwarg(), 2)])
def test_transparency(log_to_print, test_input, expected):
    assert tracecall(logger=logging)(test_input)() == expected

@pytest.mark.parametrize('test_input, expected',
                        [(lambda : A().return_1(), 1),
                         (lambda : A().return_a(1), 1),
                         (lambda : A().return_kwarg(2, a=1), 1),
                         (lambda : A().return_multiple(1, 2), (1, 2, 3)),
                         (lambda : A().return_optkwarg(1), 1),
                         (lambda : A().return_optkwarg(), 2)])
def test_transparency_class(log_to_print, test_input, expected):
    assert test_input() == expected
