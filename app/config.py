import os

from .utils.constants import INSTANCE_FOLDER_PATH


class BaseConfig(object):
  PROJECT = "CORAE"
  
  DEBUG = False
  TESTING = False

  LOGS_FOLDER_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'logs')

  MAX_CONTENT_LENGTH = 200 * 1024 * 1024
  UPLOADS_FOLDER_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'uploads')
  
class DefaultConfig(BaseConfig):

    DEBUG = False

    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False