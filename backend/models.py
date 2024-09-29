from config import db, bcrypt

# bcrypt will work with hybrid_property
from sqlalchemy.ext.hybrid import hybrid_property

# serializerMixin
from sqlalchemy_serializer import SerializerMixin

#validates using  __table_args__
from sqlalchemy.orm import validates


#Regex for email
import re

# Enum for Payment varification
from sqlalchemy import Enum


#Association table: Purchase and Invoice
purchase_invoice = db.Table("purchase_invoice",
    db.Column("purchase_id", db.ForeignKey("purchases.id"), primary_key=True),
    db.Column("invoice_id", db.ForeignKey("invoices.id"), primary_key=True)
)

# Association table: Payments and Items

payment_items = db.Table("payment_items",
db.Column("payment_id", db.ForeignKey("payments.id"), primary_key=True),
db.Column("items_id", db.ForeignKey("items.id"), primary_key=True)
)


class Users(db.Model, SerializerMixin):
    __tablename__ = "users"

    __mapper_args__ ={
        "polymophic_on": "type",
    }

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    username = db.Column(db.String(), nullable=False, unique=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    _password_hash = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(), nullable=False)   #Adimn or Staff
    permissions = db.Column(db.Text)    #Rights stored in JSON format


    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"   #Constants defined with capital letters

    @validates('email', "username")
    def validate_email(self, key, value):
        """
            Validates email at the database level before storing
        """

        if key == "email" and not re.match(self.EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        
        if key == "username" and len(value) <= 3:
            raise ValueError("Username must be at least more that 3 characters long")
        return value



    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, new_password):
        self._password_hash = bcrypt.generate_password_hash(new_password).encode("utf-8")
        
    def authenticate_password(self, user_password):
        return bcrypt.check_password_hash(self._password_hash, user_password.encode("utf-8"))
    
    def __repr__(self):
        return f"<Users {self.first_name} {self.last_name} {self.type}>"
    

class Admin(Users):

    __tablename__ = "admins"
    
    __mapper_args__ = {
        "polymorphic_identity": "Admin"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.permissions = {
            'vendor': ['C', 'R', 'U', 'D'],   # Admin can Create, Read, Update, Delete vendors
            'customer': ['C', 'R', 'U', 'D'],  
            'invoice': ['C', 'R', 'U', 'D'],  
            'purchase': ['C', 'R', 'U', 'D'],  
            'local_purchase_order': ['C', 'R', 'U', 'D'],  
            'item': ['C', 'R', 'U', 'D'],  
            'category': ['C', 'R', 'U', 'D'],  
            'serial_number': ['C', 'R', 'U', 'D'],  
            'quotation': ['C', 'R', 'U', 'D'],  
            'payment': ['C', 'R', 'U', 'D'],  
            'delivery': ['C', 'R', 'U', 'D'],  
            'currency': ['C', 'R', 'U', 'D']
            }


class Staff(db.Model, Users):

    __tablename__ = "staffs"

    __mapper_args__ = {
        "polymorphic_identity": "Staff"
    }

    date_employed = db.Column(db.Date, nullable=False)
    department = db.Column(db.String(), nullable=False)
    date_exited = db.Column(db.Date(), nullable=True)

    def __init__(self, date_employed, department, date_exited=None,  **kwargs):     #date_employed, department and date_exited are specif attributes hence in the constructor
        super().__init__(**kwargs)
        self.permissions = {
            'vendor': ['C', 'R', 'U'],   # Staff can only Create, Read, Update vendors (no delete)
            'customer': ['C', 'R', 'U'],
            'invoice': ['C', 'R', 'U'],
            'purchase': ['C', 'R', 'U'],
            'local_purchase_order': ['C', 'R', 'U'],
            'item': ['C', 'R', 'U'],
            'category': ['C', 'R', 'U'],
            'serial_number': ['C', 'R', 'U'],
            'quotation': ['C', 'R', 'U'],
            'payment': ['C', 'R', 'U'],
            'delivery': ['C', 'R', 'U'],
            'currency': ['C', 'R', 'U']
            }
        self.date_employed = date_employed
        self.date_exited = date_exited
        self.department = department


# Customer class
class Customer(db.Model, SerializerMixin):
    __table_name__ = "customers"
    

    id =db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False, index=True, unique=True)
    email = db.Column(db.String(), nullable=False, unique=True)
    phone = db.Column(db.Integer(), nullable=False, unique=True)
    kra_pin = db.Column(db.String(),nullable=True, unque=True, index=True)
    location = db.Column(db.String())
    country = db.Column(db.String(), default="Kenya")
    currency = db.Column(db.String(), nullable=False, default="KSHS")
    date_enrolled = db.Column(db.DateTime(), default= db.func.current_timestamp())
    date_last_updated = db.Column(db.DateTime(), default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    active = db.Column(db.Boolean(), default=True, nullable=False)
    account_limit = db.Column(db.Integer(), default=0, nullable=False)


    #foreignKey
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)  #Admin
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id", nullable=False))  #staff


    #serialize
    serialize_only =(name, email, phone, kra_pin)

    # regex Constant for mail
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"   #Constants defined with capital letters

    #validate
    @validates("email", "name")
    def validations(self, key, value):
        if key == "email" and not re.match(self.EMAIL_REGEX, value):
            raise ValueError("Invalid Email address ")
        
        elif key == "name" and value < 3:
            raise ValueError("Name must be at least 3 characters long")
        
        return value
    

    #Relationship
    admin = db.relationship("Admin", backref="customers", lazy=True)
    staff = db.relationship("Staff", backref="customers", lazy=True)
    
#Vendor class
class Vendor(db.Model, SerializerMixin):

    __tablename__ = "vendors"

    id = db.Column(db.Integer(), primary_key=True, nullable=False, unique=True)
    name = db.Column(db.String(), nullable=False, unique=True, index=True)
    email = db.Column(db.String(), nullable=False, unique=True, index=True)
    phone = db.Column(db.Integer(), nullable= False, unique=True)
    kra_pin = db.Column(db.String(), nullable= True, unique=True, index=True)
    location = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), default="Kenya")
    currency = db.Column(db.String(), nullable=False, default="KSHS")
    date_registered = db.Column(db.Date(), default=db.current_timestamp())
    active = db.Column(db.boolean())

    #email validation
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"   #Constants defined with capital letters

    @validates("email", "name")
    def validations(self, key, value):
        if key == "email" and not re.match(self.EMAIL_REGEX, value):
            raise ValueError( "Invalide email address")
        
        if key == "name" and value < 3:
            raise ValueError("Name must be at least 3 letters")
        return value
    
    #foreign key
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("staffs.id"), nullable=False)


    #serialize
    serialize_only = (name, email, phone, kra_pin)


    #Relationship
    admin = db.relationship("Admin", backref="vendors", lazy=True)
    staff = db.relationship("Staff", backref="staffs", lazy=True)


#Invoice
class Invoice(db.Model, SerializerMixin):
    
    __tablename__ = "invoices"

    id = db.Column(db.Integer(), primary_key=True, unique=True)
    invoice_number = db.Column(db.Integer(), nullable=False, unique=True)
    date_created = db.Column(db.Date(), default= db.current_timestamp(), nullable=False)
    days_until_due = db.Column(db.Integer(), default= 30)
    due_date = db.Column(db.Date, server_default= db.func.date(db.fun.current_date(), "+30 days"))
    notes = db.Column(db.String(), nullable=True)
    

    
    #Foreign Key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)
    currency_id = db.Column(db.Integer(), db.ForeignKey("currencies.id"), nullable=False) #one currency can have multiple invoices
    customer_id = db.Column(db.Integer(), db.ForeignKey("customers.id"), nullable=False)
    
    



    #Relationship
    admin =db.relationship("Admin", backref="invoices", lazy=True)
    staff = db.relationship("Staff", backref="invoices", lazy=True)
    currency = db.relationship("Currency", backref="invoices", lazy=True)
    customer = db.relationship("Customer", backref="invoices", lazy=True)
    purchases = db.relationship("Purchase", secondary="purchase_invoice", backref="invoices", lazy=True)
    




    def __init__(self, creator, days_until_due=None) -> None:

        """
        Initialize an Invoice: It expects either Admin or Staff instance for 'creator'

        :param creator: Either an Admin or Staff instance created the invoice

        :param days_until_due: optional, customize the number of days until the invoice is due. 
        """

        if isinstance(creator, Admin):
            self.admin_id = creator.id

        elif isinstance(creator, Staff):
            self.staff_id = creator.id

        else:
            raise ValueError("Creator must be an Admin or Staff")

        if days_until_due is not None:
            self.days_until_due = days_until_due
            self.due_date = db.func.date(self.date_created, f"+{self.days_until_due} days")
            self.invoice_number = self.generate_invoice_number()
    
    
    #Apply table constraint to the column that fills if its either Admin or Staff who created a specific Invoice
    __table_args__ ={
        db.CheckConstraint(
            "admin_id IS NOT NULL OR staff_id IS NOT NULL", name= "check_admin_or_staff"
        ),
    }

    #serialize 
    serialize_only = (invoice_number, date_created, days_until_due, due_date)

    def generate_invoice_number(self):
        """
        Purpose: function that will auto increment the invoice_number
        """

        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()

        if last_invoice:
            return last_invoice.invoice_number + 1
        return 700000


#Purchase 
class Purchase(db. Model, SerializerMixin):

    __tablename__ = "purchases"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    purchase_number = db.Column(db.Integer(), nullable=False)
    date_purchased = db.Column(db.Date, nullable=False, default=db.func.current_timestamp())
    date_due = db.Column(db.Date, nullable=False)
    delivered_by = db.Column(db.String(), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)


    #Serialize
    serialize_only =(purchase_number, date_purchased, date_due, delivery_date, delivered_by)

    #Foreign Key
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=False)
    lpo_id = db.Column(db.Integer(), db.ForeignKey("lpos.id"), nullable=True)
    



    #Relationship
    vendor = db.relationship("Vendor", backref="purchases", lazy=True)
    lpo = db.relationship("LPO", backref="purchases", lazy=True)
    invoices = db.relationship("Invoice", secondary="purchase_invoice", backref="purchases", lazy=True)


#Item
class Item(db.Model, SerializerMixin):
    __tablename__ = "items"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    description = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    vat = db.Column(db.Float(), nullable=True)
    discount = db.Column(db.Float(), nullable=True)
    total = db.Column(db.Float(), nullable=False)

    #serialize
    serialize_only = (description,quantity,price,amount,vat, discount,total)

    #Foreign Key
    invoice_id = db.Column(db.Integer(), db.ForeignKey("invoices.id"), nullable=False)
    category_id = db.Column(db.Integer(), db.ForeignKey("categories.id"), nullable=False)
    serial_number_id = db.Column(db.Integer(), db.ForeignKey("serial_numbers.id"), nullable=False, unique=True)
    currency_id = db.Column(db.Integer(), db.ForeignKey("currencies.id"), nullable=False)
    purchase_id = db.Column(db.Integer(), db.ForeignKey("purchases.id"), nullable=False)
    lpo_id = db.Column(db.Integer(),db.ForeignKey("lpos.id"))



    #Relationship
    invoice = db.relationship("Invoice", backref ="items", lazy=True)
    category = db.relationship("Category", backref="items", lazy=True)
    currency = db.relationship("Currency", backref="items", lazy=True)
    purchase =db.relationship("Purchase", backref="items", lazy=True)
    lpo = db.relationship("Lpo", backref="items", lazy=True)
    payment = db.relationship("Payment", secondary="payment_items", backref="items", nullable=False, lazy=True)


    #for different instances
    def __init__(self, category_id, description, serial_number_id, quantity, price, vat_percentage, currency_id):
        self.category_id = category_id
        self.description =description
        self.serial_number_id = serial_number_id
        self.quantity = quantity
        self.price = price
        self.amount =self.calculate_amount()
        self.vat = self.calculate_vat(vat_percentage)
        self.total = self.calculate_total()
        self.currency_id = currency_id 
        
    #calculate Amount
    def calculate_amount(self):
        return self.quantity * self.price

    #calculate vat
    def calculate_vat(self, vat_percentage):
        return (vat_percentage / 100) *self.amount
    
    #calculate the total amount
    def calculate_total(self):
        return self.amount + self.vat
    
    #exchange rate change
    def update_currency(self, exchange_rate):
        self.amount *= exchange_rate
        self.vat *= exchange_rate
        self.total = self.amount + self.vat


#Category
class Category(db.Model, SerializerMixin):
    __tablename__ = "categories"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name = db.Column(db.String(), nullable=False)


#Serial numbers for each product
class SerialNumber(db.Model, SerializerMixin):
    __tablename__ = "serial_numbers"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    serial = db.Column(db.String(), nullable=False, unique=True, index=True)

    #serialize
    serialize_only = (serial,)

    #relationship
    item = db.relationship("Item", backref="serial_number", uselist=False, lazy=True)
    

#Currency
class Currency(db.Model, SerializerMixin):
    __tablename__ = "currencies"

    id = db.Column(db.Integer(), primary_key=True, unique=True)
    name = db.Column(db.String(), nullable=False, )
    symbol = db.Column(db.String(), nullable=False, unique=True)
    exchange_rate = db.Column(db.Float(), nullable=False)


#LPO
class Lpo(db.Model, SerializerMixin):
    __tablename__ = "lpos"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    lpo_number = db.Column(db.Integer(), nullable=False, unique=True)
    date_issued = db.Column(db.Date, default=db.current_timestamp())
    days_until_due = db.Column(db.Date(), default=30)
    date_due = db.Column(db.Date(), server_default=db.func.date(db.fun.current_date(), "+30 days"))


    #Foreign Key
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=False)


    #Relationship
    vendor = db.relationship("Vendor", backref="lpos", lazy=True)


    #Initialization
    def __init__(self, days_until_due=None):
        if days_until_due is not None:
            self.days_until_due=days_until_due
            self.date_due = db.func.day(self.date_issued, f"+{self.days_until_due} days")
        


    #Function to auto increment LPO number
    def lpo_number_increment(self, instance):
        if isinstance(instance, Lpo):
            instance.lpo_number = instance.id + 1
        return 3000

# PaymentModeEnum 
class PaymentModeEnum(Enum):
    CASH = "cash"
    MPESA = "mpesa"
    BANK_TRANSFER = "bank_transfer"
    CHEQUE ="cheque"
    BANK_DEPOSIT = "bank_deposit"
    OTHERS = "others"


#Payment
class Payment(db.Model, SerializerMixin):
    __tablename__ = "payments"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    payment_mode = db.Column(Enum(PaymentModeEnum), nullable=False)
    date_paid = db.Column(db.Date(), default= db.date.current_timestamp())
    payment_reference = db.Column(db.String(), nullable=True)

    #serialize
    serialize_only = (payment_mode, date_paid, payment_reference)

    
    #Foreign Key
    invoice_id = db.Column(db.Integer(), db.ForeignKey("invoices.id"), nullable=False)
    purchase_id = db.Column(db.Integer(), db.ForeignKey("purchases.id"), nullable=True)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=False)
    customer_id = db.Column(db.Integer(), db.ForeignKey("customers.id"), nullable=False)




    #Relationship
    invoice = db.relationship("Invoice", backref="payments", lazy=True)
    purchase = db.relationship("Purchase", backref="payments", lazy=True)
    staff = db.relationship("Staff", backref="payments", lazy=True)
    admin= db.relationship("Admin", backref="payments", lazy=True)
    vendor = db.relationship("Vendor", backref="payments", lazy=True)
    customer = db.relationship("Customer", backref="payments", lazy=True)
    items = db.relationship("Item", secondary="payment_items", backref="payments", nullable=False, lazy=True)


# Quotation
class Quotation(db.Model, SerializerMixin):


