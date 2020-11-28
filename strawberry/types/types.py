import dataclasses
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from strawberry.permission import BasePermission

if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver
    from strawberry.types.types_new.type import StrawberryType

undefined = object()


@dataclasses.dataclass
class FederationTypeParams:
    keys: List[str] = dataclasses.field(default_factory=list)
    extend: bool = False


@dataclasses.dataclass
class TypeDefinition:
    name: str
    is_input: bool
    is_interface: bool
    is_generic: bool
    origin: Type
    description: Optional[str]
    federation: FederationTypeParams
    interfaces: List["TypeDefinition"]

    _fields: List["FieldDefinition"]
    _type_params: Dict[str, Type] = dataclasses.field(default_factory=dict, init=False)

    def get_field(self, name: str) -> Optional["FieldDefinition"]:
        return next((field for field in self.fields if field.name == name), None)

    @property
    def fields(self) -> List["FieldDefinition"]:
        # from .type_resolver import _resolve_types

        return self._fields

        # return _resolve_types(self._fields)

    @property
    def type_params(self) -> Dict[str, Type]:
        if not self._type_params:
            from .type_resolver import _get_type_params

            self._type_params = _get_type_params(self.fields)

        return self._type_params


@dataclasses.dataclass
class ArgumentDefinition:
    name: Optional[str] = None
    origin_name: Optional[str] = None
    type: Optional["StrawberryType"] = None
    origin: Optional[Type] = None
    child: Optional["ArgumentDefinition"] = None
    is_subscription: bool = False
    is_child_optional: bool = False
    description: Optional[str] = None


@dataclasses.dataclass
class FederationFieldParams:
    provides: List[str] = dataclasses.field(default_factory=list)
    requires: List[str] = dataclasses.field(default_factory=list)
    external: bool = False


@dataclasses.dataclass
class FieldDefinition:
    name: Optional[str]
    origin_name: Optional[str]
    type: Optional["StrawberryType"]
    origin: Optional[Union[Type, Callable]] = None
    child: Optional["FieldDefinition"] = None
    is_subscription: bool = False
    is_child_optional: bool = False
    federation: FederationFieldParams = dataclasses.field(
        default_factory=FederationFieldParams
    )
    arguments: List[ArgumentDefinition] = dataclasses.field(default_factory=list)
    description: Optional[str] = None
    base_resolver: Optional["StrawberryResolver"] = None
    permission_classes: List[Type[BasePermission]] = dataclasses.field(
        default_factory=list
    )
    deprecation_reason: Optional[str] = None
