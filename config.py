import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or ""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
class DevelopementConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    
class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or ''

config = {
    "developement": DevelopementConfig,
    "production": ProductionConfig,
    "default": DevelopementConfig
}
