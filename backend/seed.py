from config import app, db
from models import Users, Admin, Staff, Customer, Vendor, Invoice, Purchase, Item, Category, SerialNumber, Currency, Lpo, Payment, Quotation, DeliveryNote, JobCard
from faker import Faker



fake = Faker()


with app.app_context():
    pass