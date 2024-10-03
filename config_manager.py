import configparser
import os

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.set_defaults()

    def set_defaults(self):
        self.config['TRACKING'] = {
            'sensitivity': '3',
            'blink_threshold': '0.2',
            'blink_duration': '0.3',
            'mouth_open_threshold': '30',
            'mouth_open_duration': '0.5',
            'tilt_threshold': '10',
            'scroll_speed': '20'
        }
        self.save_config()

    def get_value(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def set_value(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)