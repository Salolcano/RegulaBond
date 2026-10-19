"""Minimal in-memory stand-in for the `genlayer` SDK.

It exists only so the contract's Python logic (state machine, accounting,
access checks) can be exercised locally. It does NOT model validator
consensus, equivalence principles, gas, or real GEN transfers. Studio
compilation and a live consensus transaction are still required.
"""
import importlib.util
import sys
import types
from pathlib import Path

CONTRACT = Path(__file__).parents[1] / "contracts" / "regulabond.py"


class UserError(Exception):
    pass


class u256(int):
    pass


class Address:
    def __init__(self, value):
        self.as_hex = value


class TreeMap(dict):
    def __class_getitem__(cls, item):
        return cls


class Contract:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        for klass in cls.__mro__:
            for name, ann in getattr(klass, "__annotations__", {}).items():
                if ann is TreeMap and name not in obj.__dict__:
                    obj.__dict__[name] = TreeMap()
        return obj


class _Decorator:
    def __call__(self, fn):
        return fn

    def payable(self, fn):
        return fn


class _Env:
    """Mutable test environment: caller, attached value, page/model output."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.sender = "0xsponsor"
        self.value = 0
        self.page = "Official page text"
        self.model_output = "SUPPORTS_REQUIREMENT"
        self.transfers = []


ENV = _Env()


class _Message:
    @property
    def sender_address(self):
        return Address(ENV.sender)

    @property
    def value(self):
        return u256(ENV.value)


def _contract_interface(cls):
    class Proxy:
        def __init__(self, address):
            self.address = address

        def emit_transfer(self, value=0):
            ENV.transfers.append((self.address.as_hex, int(value)))

    return Proxy


def _install():
    gl = types.SimpleNamespace()
    gl.Contract = Contract
    gl.public = types.SimpleNamespace(write=_Decorator(), view=lambda fn: fn)
    gl.message = _Message()
    gl.vm = types.SimpleNamespace(UserError=UserError)
    gl.evm = types.SimpleNamespace(contract_interface=_contract_interface)
    gl.eq_principle = types.SimpleNamespace(strict_eq=lambda fn: fn())
    gl.nondet = types.SimpleNamespace(
        web=types.SimpleNamespace(render=lambda url, mode="text": ENV.page),
        exec_prompt=lambda task: ENV.model_output,
    )
    module = types.ModuleType("genlayer")
    module.gl = gl
    module.TreeMap = TreeMap
    module.u256 = u256
    module.Address = Address
    sys.modules["genlayer"] = module


_counter = 0


def new_contract():
    """Load a fresh copy of the contract source and return an instance."""
    global _counter
    _install()
    ENV.reset()
    _counter += 1
    spec = importlib.util.spec_from_file_location(f"regulabond_under_test_{_counter}", CONTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.RegulaBond()
