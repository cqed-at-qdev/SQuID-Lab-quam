import json
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal

from quam.core import QuamComponent, quam_dataclass

__all__ = ["Information", "QuamMetadata"]

FRIDGES = ("meso", "archi", "T5", "T3", "T2")


N_DRIVE_PATHS = (Path("N:"), Path("unicph.domain\groupdir"))
SUBJECT_ID_DATABASE = Path(
    r"N:\SCI-NBI-QDev\SQuID Lab Data\Devices\name_ID_mapping.json"
)


@quam_dataclass
class Information(QuamComponent):
    """Information about the QuAM instance"""

    user_name: str = None
    user_ku_tag: str = None
    device_name: str = None
    fridge_name: Literal["meso", "archi", "T5", "T3", "T2"] = None
    state_path: str = None
    data_path: str = "#./squid_lab_data_path"
    calibration_db_path: str = "#./parent_of_state_path"

    def print_info(self):
        name = (
            f"{self.user_name} ({self.user_ku_tag})"
            if self.user_ku_tag
            else self.user_name
        )
        print(f"User name: {bold_font(name)}")
        print(f"Device name: {bold_font(self.device_name)}")
        print(f"Fridge name: {bold_font(self.fridge_name)}")

    @property
    def parent_of_state_path(self) -> str:
        return str(Path(self.state_path).parent)

    @property
    def squid_lab_data_path(self) -> str:
        return data_path_from_device_name(
            self.device_name,
            data_folder_path=Path("SCI-NBI-QDev\SQuID Lab Data\Devices"),
            main_drive_paths=N_DRIVE_PATHS,
            main_drive_name="N:drive",
        )

    @property
    def device_subjectID(self) -> str:
        return subjectID_from_database(self.device_name, SUBJECT_ID_DATABASE)


@quam_dataclass
class QuamMetadata(QuamComponent):

    unit: str = None
    long_name: str = None
    description: str = None
    last_updated: str = str(datetime.now())
    uncertainty: float = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self._initial_info = self.__dict__.copy()  # copy of the initial info

    def update_last_updated(self):
        """Update the last_updated field to the current time"""
        self.last_updated = str(datetime.now())

    @property
    def name(self) -> str:
        # name = self.parent.get_attr_name(self)
        # if not name.endswith("__metadata"):
        #     raise ValueError(
        #         f"Metadata parameter name {name} does not end with '__metadata'"
        #     )
        # return name

        return get_quam_info_name(self)

    @property
    def parameter_name(self) -> str:
        return self.name.removesuffix("__metadata")

    @property
    def value(self):
        return getattr(self.parent, self.parameter_name)

    @classmethod
    def get_metadata(cls, component: QuamComponent, attr: str) -> "QuamMetadata":
        """Get the metadata object for an attribute of a component"""
        metadata_name = f"{attr}__metadata"
        return getattr(component, metadata_name)

    def print_info(self, include_updates: bool = True):
        print(get_info_str(self, include_updates))

    def get_info_str(self, include_updates: bool = True):
        return get_info_str(self, include_updates)


def get_info_str(info: QuamMetadata, include_updates: bool = True):
    """
    Wanted print format, self.print_info():
        [value_nanme] ([long_name/optional]): [value] (±[uncertainty/optional]) [unit/optional] - [last_update/optional]
        f_01 (Qubit Frequency (01)): 5.1 ± 0.1 GHz - 2021-09-02

    Wnated print format, self.print_info(include_updates=True):
        [value_nanme] ([long_name/optional]): [value] (±[uncertainty/optional]) [unit/optional] - [last_update/optional]
        f_01 (Qubit Frequency (01)): 5.1 ± 0.1 GHz - 2021-09-02
            value: 5.0 ± 0.2 -> 5.1 ± 0.1
            last_update: 2021-09-01 -> 2021-09-02

    """
    # Construct the base output string with checks for optional fields
    base_output = f"{info.parameter_name}"

    base_output += f" ({info.long_name})" if info.long_name else ""
    base_output += f": {info.value}"
    base_output += f" ± {info.uncertainty}" if info.uncertainty is not None else ""
    base_output += f" {info.unit}" if info.unit else ""
    base_output += f" - {info.last_updated}" if info.last_updated else ""

    # Include updates if requested
    if include_updates:
        for key, value in info.__dict__.items():
            if key in info._initial_info and info._initial_info[key] != value:
                initial_value = (
                    info._initial_info[key] or "None"
                )  # Handle None for initial value
                updated_value = value or "None"  # Handle None for updated value
                base_output += f"\n\t{key}: {initial_value} -> {updated_value}"

    return base_output


def get_quam_info_name(info):
    for key, value in info.parent.__dict__.items():
        if value == info:
            return key
    raise ValueError("info should be a QuamMetadata object")


def data_path_from_device_name(
    device_name: str,
    data_folder_path: Path,
    main_drive_paths: Iterable[Path],
    main_drive_name: str,
) -> str:
    """Generates a data path from a device name of the form:
    main_drive_path / data_folder_path / device_name / "OPX Data" .
    main_drive_paths is a list of possible main drive paths, .e.g.,
    the UCPH N:drive has different paths on different computers.
    The first existing path is used.
    If the device name contains '/' or '\ ', the path is split into subfolders.

    Args:
        device_name (str): name of the device
        data_folder_path (Path): path to the data folder from the main drive
        main_drive_paths (Iterable[Path]): list of possible main drive paths
        main_drive_name (str): name of the main drive (used for error message)

    Returns:
        str: the data path

    Raises:
        FileNotFoundError: if the main drive path is not found
        FileNotFoundError: if the data folder path is not found
    """

    def _get_main_drive_path() -> Path:
        if not any(os.path.exists(drive_path) for drive_path in main_drive_paths):
            raise FileNotFoundError(
                f"Could not find data path. {main_drive_name} not found"
            )
        return next(
            drive_path for drive_path in N_DRIVE_PATHS if os.path.exists(drive_path)
        )

    main_drive_path = _get_main_drive_path()

    if not os.path.exists(main_drive_path / data_folder_path):
        raise FileNotFoundError(
            f"Could not find data path. {data_folder_path} not found. Ensure that you have access to {data_folder_path}"
        )

    return str(main_drive_path / data_folder_path / Path(device_name) / "OPX Data")


def subjectID_from_database(device_name: str, database_path: Path) -> str:
    """Get the NQCP subject ID from the device name database.
    See https://dev.azure.com/NQCP/NQCP/_wiki/wikis/NQCP.wiki/133/SubjectID for more information.

    Args:
        device_name (str): Name of the device
        database_path (Path): Path to the database file

    Raises:
        FileNotFoundError: If the database file is not found
        ValueError: If the device name is not found in the database

    Returns:
        str: NQCP Subject ID
    """
    if not os.path.exists(database_path):
        raise FileNotFoundError(f"Database file not found at {database_path}")

    with open(SUBJECT_ID_DATABASE, "r") as f:
        database = json.load(f)
        if device_name not in database:
            raise ValueError(
                f"Device name {device_name} not found in database at {database_path}"
            )

    return database[device_name]


def bold_font(text: str) -> str:
    """Make the text bold in the terminal.

    Args:
        text (str): text to make bold

    Returns:
        str: the bold text
    """
    return f"\033[1m{text}\033[0m"


if __name__ == "__main__":
    from squid_lab_quam.components.roots import SQuIDRoot1

    quam = SQuIDRoot1()
    quam.test__metadata = QuamMetadata(unit="GHz", long_name="Qubit Frequency (01)")
    quam.test = 5.1

    quam.test__metadata.print_info()
    print()

    quam.test__metadata.unit = "MHz"
    quam.test__metadata.print_info()
