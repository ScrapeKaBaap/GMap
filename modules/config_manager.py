import configparser
import os

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        # Use current working directory for relative paths, or absolute path if provided
        if os.path.isabs(config_file):
            self.config_file = config_file
        else:
            self.config_file = os.path.join(os.getcwd(), config_file)
        self.config.read(self.config_file)

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=None):
        return self.config.getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=None):
        return self.config.getint(section, option, fallback=fallback)

    def getfloat(self, section, option, fallback=None):
        return self.config.getfloat(section, option, fallback=fallback)


