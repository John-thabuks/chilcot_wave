from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import MetaData
from flask_uploads import UploadSet, configure_uploads
import os

# Flask
app = Flask(__name__)

metadata = MetaData()

#Configuring PDFs files upload for vat_file and delivery_file
app.config["UPLOADED_INVOICE_DEST"] = "uploads/invoices"    # Folder for Invoice PDFs
app.config["UPLOADED_DELIVERY_DEST"] = "uploads/delivery"   # Folder for Delivery PDFs

invoice_files = UploadSet("invoice", ("pdf",))  # Restrict to PDFs for invoices
delivery_file = UploadSet("delivery", ("pdf",))

configure_uploads(app, (invoice_files, delivery_file))

# Ensure directories exist
os.makedirs(app.config["UPLOADED_INVOICE_DEST"], exist_ok=True)
os.makedirs(app.config["UPLOADED_DELIVERY_DEST"], exist_ok=True)

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

