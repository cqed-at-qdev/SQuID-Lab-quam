from quam.core import QuamComponent, quam_dataclass


@quam_dataclass
class Information(QuamComponent):
    """Information about the QuAM instance"""

    user_name: str = None
    user_ku_tag: str = None
    device_name: str = None
    fridge_name: str = None
    data_path: str = None
    state_path: str = None

    def print_info(self):
        name = (
            f"{self.user_name} ({self.user_ku_tag})"
            if self.user_ku_tag
            else self.user_name
        )
        print(f"User name: {bold_font(name)}")
        print(f"Device name: {bold_font(self.device_name)}")
        print(f"Fridge name: {bold_font(self.fridge_name)}")


def bold_font(text: str):
    return f"\033[1m{text}\033[0m"
