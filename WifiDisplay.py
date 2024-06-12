import pwnagotchi.plugins as plugins
import pwnagotchi.ui.fonts as fonts
from pwnagotchi.ui.components import LabeledValue
from pwnagotchi.ui.view import BLACK
import logging
import os
import time

class WifiDisplay(plugins.Plugin):
    __author__ = "@8_bit_block_head (using chat gpt)"
    __version__ = "1.0.0"
    __license__ = "GPL3"
    __description__ = "A plugin to display closest cracked network & its password. Complete inspiration (and maybe some code) from crackhouse.py by @V0rT3x."
    __name__ = "WifiDisplay"
    __dependencies__ = {
        "apt": ["none"],
        "pip": ["requests"],
    }
    __defaults__ = {
        "enabled": False,
        "orientation": "vertical",
        "files": [
            "/root/handshakes/wpa-sec.cracked.potfile",
            "/root/handshakes/my.potfile",
            "/root/handshakes/OnlineHashCrack.cracked",
        ],
        "saving_path": "/root/handshakes/WifiDisplay.potfile",
        "display_stats": True,
    }

    def __init__(self):
        self.ready = False
        self.crack_menu = {}
        self.best_rssi = -1000
        self.best_crack = ["", ""]
        self.total_crack = 0
        self.time_wifi_update = "00:00"
        logging.debug(f"[{self.__class__.__name__}] plugin init")

    def on_loaded(self):
        logging.debug(f"[{self.__class__.__name__}] on_loaded called")
        self.load_passwords()
        self.ready = True
        logging.info(f"[{self.__class__.__name__}] Successfully loaded and ready")

    def load_passwords(self):
        logging.debug(f"[{self.__class__.__name__}] load_passwords called")
        crack_list = []
        for file_path in self.options["files"]:
            logging.debug(f"[{self.__class__.__name__}] Reading file {file_path}")
            if os.path.exists(file_path):
                with open(file_path) as f:
                    for line in f:
                        if ":" in line:
                            parts = line.strip().split(":")
                            if len(parts) >= 4:
                                ssid = parts[2]
                                password = parts[3]
                                crack_list.append(f"{ssid}:{password}")
                                self.crack_menu[ssid] = password
            else:
                logging.warning(f"[{self.__class__.__name__}] File {file_path} does not exist")

        self.save_WifiDisplay_potfile(crack_list)
        logging.info(f"[{self.__class__.__name__}] Loaded passwords from files: {self.crack_menu}")

    def save_WifiDisplay_potfile(self, crack_list):
        with open(self.options["saving_path"], "w") as f:
            for crack in crack_list:
                f.write(crack + "\n")
        logging.info(f"[{self.__class__.__name__}] Saved WifiDisplay.potfile with entries: {crack_list}")

    def on_ui_setup(self, ui):
        logging.debug(f"[{self.__class__.__name__}] on_ui_setup called")
        position = self.get_position(ui)
        ui.add_element(
            "WifiDisplay",
            LabeledValue(
                color=BLACK,
                label="",
                value="",
                position=position,
                label_font=fonts.Bold,
                text_font=fonts.Small,
            ),
        )
        if self.options["display_stats"]:
            ui.add_element(
                "WifiDisplay_stats",
                LabeledValue(
                    color=BLACK,
                    label="Stats",
                    value="",
                    position=(position[0], position[1] + 20),
                    label_font=fonts.Bold,
                    text_font=fonts.Small,
                ),
            )
        logging.debug(f"[{self.__class__.__name__}] UI elements added")

    def get_position(self, ui):
        if ui.is_waveshare_v4():
            return (0, 95) if self.options["orientation"] == "horizontal" else (180, 61)
        elif ui.is_waveshare_v1():
            return (0, 95) if self.options["orientation"] == "horizontal" else (170, 61)
        elif ui.is_waveshare144lcd():
            return (0, 92) if self.options["orientation"] == "horizontal" else (78, 67)
        elif ui.is_inky():
            return (0, 83) if self.options["orientation"] == "horizontal" else (165, 54)
        elif ui.is_lcdhat():
            return (0, 203) if self.options["orientation"] == "horizontal" else (-10, 185)
        elif ui.is_waveshare27inch():
            return (0, 153) if self.options["orientation"] == "horizontal" else (216, 122)
        else:
            return (0, 91) if self.options["orientation"] == "horizontal" else (180, 61)

    def on_unload(self, ui):
        logging.debug(f"[{self.__class__.__name__}] on_unload called")
        with ui._lock:
            try:
                ui.remove_element("WifiDisplay")
                ui.remove_element("WifiDisplay_stats")
                logging.info(f"[{self.__class__.__name__}] plugin unloaded")
            except Exception as e:
                logging.error(f"[{self.__class__.__name__}] unload: {e}")

    def on_wifi_update(self, agent, access_points):
        logging.debug(f"[{self.__class__.__name__}] on_wifi_update called with access_points: {access_points}")
        self.time_wifi_update = time.strftime("%H:%M", time.localtime())
        if self.ready and "Not-Associated" in os.popen("iwconfig wlan0").read():
            self.best_rssi = -1000
            count_crack = 0
            for network in access_points:
                ssid = network["hostname"]
                rssi = network["rssi"]
                logging.debug(f"[{self.__class__.__name__}] Checking network: {ssid} with RSSI: {rssi}")
                if ssid in self.crack_menu:
                    count_crack += 1
                    if rssi > self.best_rssi:
                        self.best_rssi = rssi
                        self.best_crack = [ssid, self.crack_menu[ssid]]
                        logging.debug(f"[{self.__class__.__name__}] Found matching crack: {self.best_crack}")
            self.total_crack = count_crack
            logging.debug(f"[{self.__class__.__name__}] Best RSSI: {self.best_rssi}, Best Crack: {self.best_crack}, Total Cracks: {self.total_crack}")

    def on_ui_update(self, ui):
        logging.debug(f"[{self.__class__.__name__}] on_ui_update called")
        if self.best_rssi != -1000:
            if self.options["orientation"] == "vertical":
                msg = f"{self.best_crack[0]} ({self.best_rssi})\n{self.best_crack[1]}"
            else:
                msg = f"{self.best_crack[0]}:{self.best_crack[1]}"
            ui.set("WifiDisplay", msg)
            logging.debug(f"[{self.__class__.__name__}] Displaying best crack: {msg}")
        else:
            last_line = "tail -n 1 /root/handshakes/WifiDisplay.potfile"
            last_crack = os.popen(last_line).read().rstrip()
            logging.debug(f"[{self.__class__.__name__}] Last crack: {last_crack}")
            ui.set("WifiDisplay", last_crack)

        if self.options["display_stats"]:
            stats_msg = f"({self.time_wifi_update}) {self.total_crack}/{len(self.crack_menu)}"
            ui.set("WifiDisplay_stats", stats_msg)
            logging.debug(f"[{self.__class__.__name__}] Displaying stats: {stats_msg}")

    def on_webhook(self, path, request):
        logging.info(f"[{self.__class__.__name__}] webhook pressed")

def register():
    return WifiDisplay()
