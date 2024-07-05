import os
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal

from quam.core import QuamComponent, quam_dataclass

FRIDGES = ("meso", "archi", "T5", "T3", "T2")
N_DRIVE_PATHS = (Path("N:"), Path("unicph.domain\groupdir"))


@quam_dataclass
class Information(QuamComponent):
    """Information about the QuAM instance"""

    user_name: str = None
    user_ku_tag: str = None
    device_name: str = None
    fridge_name: Literal["meso", "archi", "T5", "T3", "T2"] = None
    state_path: str = None
    data_path: str = "#./squid_lab_data_path"

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
    def squid_lab_data_path(self) -> str:
        return data_path_from_device_name(
            self.device_name,
            data_folder_path=Path("SCI-NBI-QDev\SQuID Lab Data\Devices"),
            main_drive_paths=N_DRIVE_PATHS,
            main_drive_name="N:drive",
        )


@quam_dataclass
class QuamMetadata(QuamComponent):

    unit: str = None
    long_name: str = None
    description: str = None
    last_updated: str = str(datetime.now())
    uncertainty: float = None

    def update_last_updated(self):
        """Update the last_updated field to the current time"""
        self.last_updated = str(datetime.now())

    def value(self):
        metadata_name = self.parent.get_attr_name(self)
        value_name = metadata_name.split("__")[-1]
        return self.parent.get_attr_value(value_name)


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


def bold_font(text: str) -> str:
    """Make the text bold in the terminal.

    Args:
        text (str): text to make bold

    Returns:
        str: the bold text
    """
    return f"\033[1m{text}\033[0m"
