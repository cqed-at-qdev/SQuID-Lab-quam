"""Module for extracting metadata from docstrings.

This module provides functionality to parse docstrings in Python code, extracting
useful metadata such as argument names, long names, units, and descriptions. It
utilizes the `docstring_parser` library to parse the docstrings and then processes
the parsed content to extract and format the metadata. This can be particularly
useful for generating documentation or for any application where metadata from
docstrings needs to be programmatically accessed and used.

Example usage:
    The module can be used to parse a docstring and extract metadata as follows:

    ```python
    docstring_content = \"\"\"
    Function description here.
    
    Args:
        param1 (int): The first parameter [m].
        param2 (str): The second parameter; An extended description [s].
    \"\"\"
    
    metadata = get_metadata_from_docstring(docstring_content)
    print(metadata)
    ```

This will output the metadata extracted from the docstring in a structured format.
"""

__all__ = ["get_metadata_of_class"]

import dataclasses
import types

from docstring_parser import DocstringParam, DocstringStyle, combine_docstrings, parse
from quam.core import QuamComponent

UNIT_DELIMITERS = ["[", "]"]
LONG_NAME_DELIMITER = ";"
LOWER_CLASS_LIMIT = (object,)


def get_unit(
    description: str | None, strip: bool = True, use_pint: bool = True
) -> str | None:
    """Extract the unit from a given description string.

    Parses the description to find a unit enclosed within predefined delimiters
    and returns the unit string, optionally stripping whitespace.

    Args:
        description: The description string from which to extract the unit.
        strip: A boolean indicating whether to strip whitespace from the unit.

    Returns:
        The extracted unit as a string, or None if no unit is found.
    """
    if (
        description
        and UNIT_DELIMITERS[0] in description
        and UNIT_DELIMITERS[1] in description
    ):
        unit = description.split(UNIT_DELIMITERS[0])[-1].split(UNIT_DELIMITERS[1])[0]
        return unit.strip() if strip else unit

    return None


def remove_unit_from_string(string: str, unit: str | None) -> str:
    """Remove the unit from the start or end of a string.

    Args:
        string: The string from which to remove the unit.
        unit: The unit to remove from the string.

    Returns:
        The string with the unit removed from the start or end.
    """
    if string and unit:
        unit_with_delimiters = UNIT_DELIMITERS[0] + unit + UNIT_DELIMITERS[1]

        if string.startswith(unit_with_delimiters):  # Remove unit from the start
            string = string[len(unit_with_delimiters) :].strip()

        elif string.endswith(unit_with_delimiters):  # Remove unit from the end
            string = string[: -len(unit_with_delimiters)].strip()

    return string


def get_long_name(description: str | None) -> str | None:
    """Extract the long name from a description string.

    Args:
        description: The description string from which to extract the long name.

    Returns:
        The extracted long name, or None if not found.
    """
    if description and LONG_NAME_DELIMITER in description:
        long_name = description.split(LONG_NAME_DELIMITER)[0]
        return remove_unit_from_string(long_name, get_unit(description, False)).strip()
    return None


def get_description(description: str | None) -> str | None:
    """Extract the description part from a description string.

    Args:
        description: The description string from which to extract the description part.

    Returns:
        The extracted description, or None if not found.
    """
    # If long name is present, extract the description part
    if description and LONG_NAME_DELIMITER in description:
        desc = description.split(LONG_NAME_DELIMITER)[1]
        return remove_unit_from_string(desc, get_unit(description, False)).strip()

    # If no long name is present, return the description as is
    if description:
        return remove_unit_from_string(
            description, get_unit(description, False)
        ).strip()

    return None


def get_parameter_metadata(
    param: DocstringParam,
) -> dict[str, str | None]:
    """Extract metadata from a DocstringParam object.

    Args:
        param: The DocstringParam object from which to extract metadata.

    Returns:
        A dictionary containing extracted metadata.
    """
    return {
        "arg_name": param.arg_name,
        "long_name": get_long_name(param.description),
        "unit": get_unit(param.description),
        "description": get_description(param.description),
        "type": param.type_name,
    }


def get_metadata_from_docstring(
    docstring: str | None,
) -> dict[str, dict[str, str | None]]:
    """Extract metadata from a docstring.

    Args:
        docstring: The docstring from which to extract metadata.

    Returns:
        A dictionary containing metadata for each parameter described in the docstring.
    """
    if docstring is None:
        return {}

    parsed = parse(docstring)
    return {param.arg_name: get_parameter_metadata(param) for param in parsed.params}


def get_metadata_of_class(obj):
    doc = combine_init_docstrings(obj)
    return get_metadata_from_docstring(doc)


def has_parents(obj):
    if obj.__bases__ == LOWER_CLASS_LIMIT:
        return False
    return QuamComponent not in obj.__bases__


def get_func_list(obj, func_list=None, docs_list=None):
    if func_list is None:
        func_list = []

    if docs_list is None:
        docs_list = []

    func_list.append(obj.__init__)
    docs_list.append(obj if dataclasses.is_dataclass(obj) else obj.__init__)

    if has_parents(obj):
        for base in obj.__bases__:
            get_func_list(base, func_list, docs_list)
    return func_list, docs_list


def get_args_from_func_list(func_list) -> set:
    args = []
    for func in func_list:
        args.extend(func.__code__.co_varnames)
    return set(args)


def combine_init_docstrings(obj):
    func_list, docs_list = get_func_list(obj)
    args = get_args_from_func_list(func_list)

    # Convert args set to a list and sort it to ensure consistent order
    args_list = sorted(list(args))

    # Create a code object with the collected arguments
    code = types.CodeType(
        0,  # argcount
        0,  # posonlyargcount
        len(args_list),  # kwonlyargcount
        len(args_list),  # nlocals
        1,  # stacksize
        67,  # flags
        b"",  # codestring
        (),  # constants
        (),  # names
        tuple(args_list),  # varnames
        "<string>",  # filename
        "placeholder_function",  # name
        1,  # firstlineno
        b"",  # lnotab
    )

    # Create the function
    placeholder_function = types.FunctionType(code, globals())

    # Apply the decorator
    return combine_docstrings(*docs_list, style=DocstringStyle.GOOGLE)(
        placeholder_function
    ).__doc__


if __name__ == "__main__":
    # Example docstring to parse
    docstring_example = """
        Frequency Converter class.
        
        Args:
            f_01 (int): [Hz] Qubit frequency (01); Frequency of the |0> to |1> transition.
            f_12 (int): Qubit frequency (12); Frequency of the |1> to |2> transition. [Hz]
            auto_update (bool): If True, the frequency of the qubit will be updated automatically.
            duration (float): Duration of the pulse. [s]
            
        Returns:
            int: The frequency of the qubit.
            """

    # Extract metadata from the example docstring
    metadata = get_metadata_from_docstring(docstring_example)
    metadata
