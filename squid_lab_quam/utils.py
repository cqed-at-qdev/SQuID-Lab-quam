from typing import Hashable

from quam.core import QuamComponent
from quam.core.quam_classes import QuamDict

__all__ = ["id_from_parent_dict"]


def key_from_parent_dict(component: QuamComponent) -> Hashable:
    """If the component is a value in a dict of its parent, return the key.

    Useful for defining the id of a component based on its parent dict, e.g.,
    by setting self.id = "#./id_from_parent_dict" along with the property:

    @property
    def id_from_parent_dict(self) -> Hashable:
        return key_from_parent_dict(self)


    Args:
        component (QuamComponent): The component to get the key for.

    Raises:
        ValueError: If the parent of the component is not a dict.

    Returns:
        Hashable: The key of the component in its parent dict.
    """

    if isinstance(component.parent, QuamDict):
        for key, value in component.parent.items():
            if value == component:
                return key
    else:
        raise ValueError(
            f"Could not find key for component {component}, parent is not a dict. "
        )
