import typing
from abc import ABC
from typing import ClassVar, Dict, ForwardRef, Generic, Optional, Tuple, Type, \
    TypeVar, Union

from cached_property import cached_property

import strawberry.utils.typing

T = TypeVar("T")


class _UNSET:
    pass


# Optional[T]: .wrapped_type should be T, with is_optional = True
# List[S, V]: .child_types should be S and V (as StrawberryTypes)

# Test cases:
#    Optional["SomeClass"]
#    "Optional[SomeClass]"
#    Optional["Optional[SomeClass]"]  # This is a silly edge case, but solving this
#                                       means we have a good solution to the problem

# TODO: Private types. Should that information be stored on the class or in the Type?


_TYPE_TYPE = Union[Type[T], str, ForwardRef]
_NAMESPACE_TYPE = Optional[Dict[str, object]]


class StrawberryType(ABC, Generic[T]):
    # TODO: Use Final in py3.8
    UNSET: ClassVar[_UNSET] = _UNSET()

    def __init__(self, type_: _TYPE_TYPE, *,
                 default: Union[T, _UNSET] = UNSET,
                 namespace: _NAMESPACE_TYPE = None):
        self._raw_type = type_
        self.default = default
        self._namespace = namespace

        # None until .resolved_type is calculated
        self._is_optional: Optional[bool] = None
        self._is_forward_ref: Optional[bool] = None

    @cached_property
    def child_types(self) -> Optional[Tuple["StrawberryType"]]:
        """Child types of the wrapped type

        Examples:
        StrawberryType(List[str]).child_types  -->  (str,)
        StrawberryType(Union[int, bool]).child_types  ->  (int, bool)
        StrawberryType(str).child_types  ->  None
        """

        if self.is_list:
            types = strawberry.utils.typing.get_list_annotation(self.wrapped_type)
        elif self.is_union:
            types = self.wrapped_type.children  # TODO
        else:
            return None

        return tuple(map(StrawberryType, types))

    @cached_property
    def wrapped_type(self) -> T:
        return self._resolved_type

    @cached_property
    def is_async_generator(self) -> bool:
        return strawberry.utils.typing.is_async_generator(self.wrapped_type)

    @cached_property
    def is_forward_ref(self) -> bool:
        _ = self._resolved_type  # make sure property evaluates
        return self._is_forward_ref

    @cached_property
    def is_generic(self) -> bool:
        return strawberry.utils.typing.is_generic(self.wrapped_type)

    @cached_property
    def is_list(self) -> bool:
        return strawberry.utils.typing.is_list(self.wrapped_type)

    @cached_property
    def is_optional(self) -> bool:
        _ = self._resolved_type  # make sure property evaluates
        return self._is_optional

    @cached_property
    def is_scalar(self) -> bool:
        return strawberry.scalars.is_scalar(self.wrapped_type)

    @cached_property
    def is_type_var(self) -> bool:
        return strawberry.utils.typing.is_type_var(self.wrapped_type)

    @cached_property
    def is_union(self) -> bool:
        return strawberry.utils.typing.is_union(self.wrapped_type)

    @cached_property
    def _resolved_type(self) -> Type[T]:
        """Resolve the type (i.e. resolve ForwardRefs and strip off Optionals"""
        type_ = self._raw_type

        # Make sure outer type is not a ForwardRef
        type_, forward_ref = self._resolve_forward_ref(type_, self._namespace)

        # Rip off Optional if it's there
        type_, optional = self._resolve_optional(type_)

        self._is_optional = optional
        self._is_forward_ref = forward_ref

        # TODO: Maybe it would be best to use some sort of loop here?
        # Do it again. This ensures that both "Optional[SomeClass]" and
        # Optional["SomeClass"] are handled
        type_, forward_ref = self._resolve_forward_ref(type_, self._namespace)
        type_, optional = self._resolve_optional(type_)

        self._is_optional = self._is_optional or optional
        self._is_forward_ref = self._is_forward_ref or forward_ref

        return type_

    @staticmethod
    def _resolve_forward_ref(type_: _TYPE_TYPE, namespace: _NAMESPACE_TYPE) \
        -> Tuple[Type[T], bool]:
        is_forward_ref = False

        if isinstance(type_, str):
            type_ = typing.ForwardRef(type_, is_argument=False)
        if isinstance(type_, ForwardRef):
            # TODO: Make sure this doesn't throw name error (or use __module__?)
            type_ = typing._eval_type(type_, namespace, None)

            is_forward_ref = True

        return type_, is_forward_ref

    @staticmethod
    def _resolve_optional(type_: Union[Type[T], Optional[Type[T]]]) \
        -> Tuple[Type[T], bool]:
        is_optional = False

        if strawberry.utils.typing.is_optional(type_):
            type_ = strawberry.utils.typing.get_optional_annotation(type_)
            is_optional = True

        return type_, is_optional
