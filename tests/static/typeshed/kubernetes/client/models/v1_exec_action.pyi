# Stubs for kubernetes.client.models.v1_exec_action (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional

class V1ExecAction:
    swagger_types: Any = ...
    attribute_map: Any = ...
    discriminator: Any = ...
    command: Any = ...
    def __init__(self, command: Optional[Any] = ...) -> None: ...
    @property
    def command(self): ...
    @command.setter
    def command(self, command: Any) -> None: ...
    def to_dict(self): ...
    def to_str(self): ...
    def __eq__(self, other: Any): ...
    def __ne__(self, other: Any): ...