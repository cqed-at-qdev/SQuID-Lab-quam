from typing import Hashable

from quam.core import QuamComponent
from quam.core.quam_classes import QuamDict, QuamList

__all__ = ["get_name_from_parent"]


def key_from_parent_dict(component: QuamComponent) -> Hashable:
    """If the component is a value in a dict of its parent, return the key.

    Useful for defining the id of a component based on its parent dict, e.g.,
    by setting self.id = "#./id_from_parent_dict" along with the property:

    @property
    def id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))


    Args:
        component (QuamComponent): The component to get the key for.

    Raises:
        ValueError: If the parent of the component is not a dict.

    Returns:
        Hashable: The key of the component in its parent dict.
    """

    if not isinstance(component.parent, (dict, QuamDict)):
        raise ValueError(
            f"Could not find key for component {component}, parent is not a dict. "
        )
    for key, value in component.parent.items():
        if value == component:
            return key

    raise ValueError(
        f"Could not find key for component {component}, parent is not a dict. "
    )


def index_from_parent_list(component: QuamComponent) -> int:
    """If the component is in a list of its parent, return the index.

    Useful for defining the id of a component based on its parent list, e.g.,
    by setting self.id = "#./id_from_parent_list" along with the property:

    @property
    def id_from_parent_list(self) -> str:
        return str(index_from_parent_list(self))


    Args:
        component (QuamComponent): The component to get the index for.

    Raises:
        ValueError: If the parent of the component is not a list.

    Returns:
        int: The index of the component in its parent list.
    """

    if not isinstance(component.parent, (list, tuple, QuamList)):
        raise ValueError(
            f"Could not find index for component {component}, parent is not a list. "
        )
    return component.parent.index(component)


def name_from_parent_component(component: QuamComponent) -> str:
    """If the component is a value in a dict of its parent, return the key.

    Useful for defining the id of a component based on its parent dict, e.g.,
    by setting self.id = "#./id_from_parent_dict" along with the property:

    @property
    def id_from_parent_dict(self) -> str:
        return str(key_from_parent_dict(self))


    Args:
        component (QuamComponent): The component to get the key for.

    Raises:
        ValueError: If the parent of the component is not a dict.

    Returns:
        Hashable: The key of the component in its parent dict.
    """

    if isinstance(component.parent, (QuamDict, QuamList)):
        raise ValueError(
            f"Parent of component {component} is a QuamDict or QuamList. (parent: {type(component.parent)})"
            "Use key_from_parent_dict or index_from_parent_list instead."
        )

    if not isinstance(component.parent, QuamComponent):
        raise ValueError(
            f"Could not find name for component {component}, parent is not a component. "
        )
    for key, value in component.parent.__dict__.items():
        if value == component:
            return key

    raise ValueError(
        f"Could not find name for component {component}, parent is not a component. "
    )


def get_parent_type(component: QuamComponent) -> type:
    return type(component.parent)


def get_name_from_parent(component: QuamComponent) -> str:
    parent_type = get_parent_type(component)

    if parent_type in (QuamDict, dict):
        return str(key_from_parent_dict(component))

    if parent_type in (QuamList, list, tuple):
        return str(index_from_parent_list(component))

    return name_from_parent_component(component)
