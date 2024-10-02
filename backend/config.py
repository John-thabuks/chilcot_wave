from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import MetaData

# Flask
app = Flask(__name__)

metadata = MetaData()

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///wave.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy()
db.init_app(app)

# Encrypt
bcrypt = Bcrypt(app)

# Migrate
migrate = Migrate(app, db)


# CORS
cors = CORS(app)

# Send request in Json
app.json.compact =False

