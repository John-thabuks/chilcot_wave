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
import enum
from sqlalchemy import Enum as SQLEnum

import json

from datetime import timedelta, datetime


#Association table: Purchase and Invoice
purchase_invoice = db.Table("purchase_invoice",
    db.Column("purchase_id",db.Integer(), db.ForeignKey("purchases.id"), primary_key=True),
    db.Column("invoice_id",db.Integer(), db.ForeignKey("invoices.id"), primary_key=True)
)


# Association table: JobCard and Invoice
jobcard_invoice = db.Table("jobcard_invoice",
    db.Column("jobcard_id",db.Integer(), db.ForeignKey("jobcards.id"), primary_key=True),
    db.Column("invoice_id",db.Integer(), db.ForeignKey("invoices.id"), primary_key=True)
)


class Users(db.Model, SerializerMixin):
    __tablename__ = "users"

    __mapper_args__ ={
        "polymorphic_on": "type",
        "polymorphic_identity": "users"
    }

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    username = db.Column(db.String(), nullable=False, unique=True)
    email = db.Column(db.String(), unique=True, nullable=False, index=True)
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

    __table_args__ = (
    db.UniqueConstraint('email', name='uq_users_email'),
)

    @hybrid_property
    def password(self):
        return self._password_hash

    @password.setter
    def password(self, new_password):
        self._password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
        
    def authenticate_password(self, user_password):
        return bcrypt.check_password_hash(self._password_hash, user_password.encode("utf-8"))
    

    @hybrid_property
    def permissions_dict(self):
        """Returns the permissions as a dictionary"""
        return json.loads(self.permissions or '{}')

    @permissions_dict.setter
    def permissions_dict(self, value):
        """Converts the permissions dictionary to a JSON string before storing"""
        self.permissions = json.dumps(value)
    

    def __repr__(self):
        return f"<Users {self.first_name} {self.last_name} {self.type}>"
    


# Currency Enum
class CurrencyEnum(enum.Enum):
    KSHS = "Kshs"
    USD = "USD"
    POUND = "Pound"
    EURO = "Euro"


# Customer class
class Customer(Users):
    __tablename__ = "customers"

    __mapper_args__ = {
        "polymorphic_identity": "Customer"
    }
    

    id =db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    # name = db.Column(db.String(), nullable=False, index=True, unique=True)
    # email = db.Column(db.String(), nullable=False, unique=True)
    phone = db.Column(db.Integer(), nullable=False, unique=True)
    kra_pin = db.Column(db.String(),nullable=True, unique=True, index=True)
    location = db.Column(db.String())
    country = db.Column(db.String(), default="Kenya")
    currency = db.Column(SQLEnum(CurrencyEnum), nullable=False, default=CurrencyEnum.KSHS)
    date_enrolled = db.Column(db.Date(), default= db.func.current_date())
    date_last_updated = db.Column(db.DateTime(), default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    active = db.Column(db.Boolean(), default=True, nullable=False)
    account_limit = db.Column(db.Integer(), nullable=False)


    #foreignKey
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=True)  #Admin
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=True)  #staff

    #initialize
    def __init__(self, name, email, phone, kra_pin, location, country, active, account_limit, instance, password, **kwargs):

        """
        Initializes the Customer instance.
        `name`, `email`, `phone`, `kra_pin`, `location`, and `country` are specific to Customer.
        `password`, `email`, and login-related fields are inherited from Users.
        """
        super().__init__(first_name = name, last_name="", username=name, email=email, _password_hash = password, **kwargs)

        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance, Staff):
            self.staff_id = instance.id
            self.admin_id =0
        else:
            raise ValueError("Must be Admin of Staff")
                
        self.phone = phone
        self.kra_pin = kra_pin
        self.location = location
        self.country = country        
        self.date_last_updated = db.func.current_timestamp()
        self.active = active
        self.account_limit = account_limit
        self.permissions_dict = {
            'invoice': ['R'],
            'delivery': ['R']
        }
        
        
    #Account limit change: Upward or Downward
    def update_account_limit(self, new_account_limit, instance):
        if not isinstance(instance, Admin):
            raise PermissionError("Only Admin can update the account limit")
        if new_account_limit < 0:
            raise ValueError("Account limit must be greater than 0")
        self.account_limit = new_account_limit
        
        self.active = new_account_limit > 0

    #serialize
    serialize_only =( "email", "phone", "kra_pin", "location","country", "currency", "date_enrolled", "date_last_updated", "active", "account_limit")

    # # regex Constant for mail
    # EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"   #Constants defined with capital letters

    # #validate
    # @validates("email", "name", "phone")
    # def validations(self, key, value):
    #     if key == "email" and not re.match(self.EMAIL_REGEX, value):
    #         raise ValueError("Invalid Email address ")
        
    #     if key == "name" and len(value) < 3:
    #         raise ValueError("Name must be at least 3 characters long")
        
    #     if key == "phone" and not value.isdigit():
    #         raise ValueError("Invalid phone number: Phone number must be a digit")
    #     return value
    

    #Relationship        
    payments = db.relationship("Payment", backref="customer", lazy=True)
    invoices = db.relationship("Invoice", backref="customer", lazy=True)



#Departments
class DepartmentEnum(enum.Enum):
    SALES = "sales"
    ACCOUNTS = "accounts"
    TECHNICAL = "technical"
    LOGISTICS = "logistics"

#EmploymentStatusEnum
class EmploymentStatusEnum(enum.Enum):
    ONGOING = "on_going"
    TERMINATED = "terminated"

class Staff( Users):

    __tablename__ = "staffs"

    __mapper_args__ = {
        "polymorphic_identity": "Staff"
    }
    id = db.Column(db.Integer(),db.ForeignKey('users.id'), primary_key=True, nullable=False)
    date_employed = db.Column(db.Date, nullable=False)
    department = db.Column(SQLEnum(DepartmentEnum), nullable=False, default=DepartmentEnum.SALES)
    employment_status = db.Column(SQLEnum(EmploymentStatusEnum), nullable=False, default=EmploymentStatusEnum.ONGOING)
    date_exited = db.Column(db.Date(), nullable=True)

    #Serialize the Staff: It automatically inherit the SerializeMixin form Users
    serialize_only = ('id', 'first_name', 'last_name', 'username', 'email', 'permissions', 'date_employed', 'department', 'employment_status')


    def __init__(self, date_employed, department, date_exited=None,  **kwargs):     #date_employed, department and date_exited are specif attributes hence in the constructor
        super().__init__(**kwargs)
        self.permissions_dict = {
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

    #Foreign Key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)


    #relationship
    jobcards = db.relationship("JobCard", backref="staff", lazy=True)
    deliverynotes = db.relationship("DeliveryNote", backref="staff", lazy=True)
    quotations = db.relationship("Quotation", backref="staff", lazy=True)
    payments = db.relationship("Payment", backref="staff", lazy=True)
    lpos = db.relationship("Lpo", backref="staff", lazy=True)
    categories = db.relationship("Category", backref="staff", lazy=True)
    purchases = db.relationship("Purchase", backref="staff", lazy=True)
    invoices = db.relationship("Invoice", backref="staff", lazy=True)
    vendors = db.relationship("Vendor", backref="staff", lazy=True)
    customers = db.relationship("Customer", foreign_keys=[Customer.staff_id],  backref="staff", lazy=True)


class Admin(Users):

    __tablename__ = "admins"
    
    __mapper_args__ = {
        "polymorphic_identity": "Admin"
    }

    id = db.Column(db.Integer(), db.ForeignKey('users.id'),primary_key=True, nullable=False)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.permissions_dict = {
            'vendor': ['C', 'R', 'U', 'D'],   # Admin can Create, Read, Update, Delete vendors
            'customer': ['C', 'R', 'U', 'D'],  
            'invoice': ['C', 'R', 'U', 'D'],  
            'purchase': ['C', 'R', 'U', 'D'],  
            'lpo': ['C', 'R', 'U', 'D'],  
            'item': ['C', 'R', 'U', 'D'],  
            'category': ['C', 'R', 'U', 'D'],  
            'serial_number': ['C', 'R', 'U', 'D'],  
            'quotation': ['C', 'R', 'U', 'D'],  
            'payment': ['C', 'R', 'U', 'D'],  
            'delivery': ['C', 'R', 'U', 'D'],  
            'currency': ['C', 'R', 'U', 'D'],
            'jobcard': ['C', 'R', 'U', 'D'],
            'deliverynote': ['C', 'R', 'U', 'D']
            }

    #relationship
    jobcards = db.relationship("JobCard", backref="admin", lazy=True)
    deliverynotes = db.relationship("DeliveryNote", backref="admin", lazy=True)
    quotations = db.relationship("Quotation", backref="admin", lazy=True)
    payments= db.relationship("Payment", backref="admin", lazy=True)
    lpos = db.relationship("Lpo", backref="admin", lazy=True)
    categories= db.relationship("Category", backref="admin", lazy=True)
    purchases = db.relationship("Purchase", backref="admin", lazy=True)
    invoices =db.relationship("Invoice", backref="admin", lazy=True)
    vendors = db.relationship("Vendor", backref="admin", lazy=True)
    customers = db.relationship("Customer", foreign_keys=[Customer.admin_id], backref="admin", lazy=True)
    staffs= db.relationship("Staff", backref="admin", lazy=True, foreign_keys=[Staff.admin_id])





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
    currency = db.Column(SQLEnum(CurrencyEnum), nullable=False, default=CurrencyEnum.KSHS.value)
    date_registered = db.Column(db.Date(), default=db.func.current_date())
    active = db.Column(db.Boolean(), default=True)

    #email validation
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"   #Constants defined with capital letters

    @validates("email", "name", "phone")
    def validations(self, key, value):
        if key == "email" and not re.match(self.EMAIL_REGEX, value):
            raise ValueError( "Invalide email address")
        
        if key == "name" and len(value) < 3:
            raise ValueError("Name must be at least 3 letters")
        
    
        if key == "phone" and not value.isdigit():
            raise ValueError("Invalid phone number: Phone number must be digits")
        
        return value
    
    #foreign key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=True)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=True)


    #serialize
    serialize_only = ("name", "email", "phone", "kra_pin")

    #initialize
    def __init__(self, name, email, phone, kra_pin, location, country, instance, currency=CurrencyEnum.KSHS) -> None:
        #Who onboarded the vendor:
        if isinstance(instance, Admin):
            self.admin_id = instance.id
        elif isinstance(instance, Staff):
            self.staff_id = instance.id
        else:
            raise ValueError("Instance must be of type Admin or Staff")
        self.name = name
        self.email = email
        self.phone = phone
        self.kra_pin = kra_pin
        self.location =location
        self.country =country
        self.currency = currency

    #Relationship
    payments = db.relationship("Payment", backref="vendor", lazy=True)
    lpos = db.relationship("Lpo", backref="vendor", lazy=True)
    purchases = db.relationship("Purchase", backref="vendor", lazy=True)


#Invoice
class Invoice(db.Model, SerializerMixin):
    
    __tablename__ = "invoices"

    id = db.Column(db.Integer(), primary_key=True, unique=True)
    invoice_number = db.Column(db.Integer(), nullable=False, unique=True, default=700000)
    date_created = db.Column(db.Date(), default= db.func.current_date(), nullable=False)
    days_until_due = db.Column(db.Integer(), default= 30)
    due_date = db.Column(db.Date(), nullable=False)
    notes = db.Column(db.String(), nullable=True)
    client_lpo_number = db.Column(db.String(), nullable=False)
    total_amount = db.Column(db.Float(), nullable=False)
    balance = db.Column(db.Float(), nullable=False, default=0.0)
    vat_file_name = db.Column(db.String(), nullable=True)
    vat_file_path = db.Column(db.String(), nullable=True)
    

    
    #Foreign Key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)
    customer_id = db.Column(db.Integer(), db.ForeignKey("customers.id"), nullable=False)
    


    #Relationship    
    purchases = db.relationship("Purchase", secondary=purchase_invoice, backref="invoice", lazy=True)
    jobcard = db.relationship   ("JobCard", secondary=jobcard_invoice, backref="invoices", lazy=True)
    deliverynotes = db.relationship("DeliveryNote", backref="invoice", lazy=True)
    payments = db.relationship("Payment", backref="invoice", lazy=True)
    items = db.relationship("Item", backref ="invoice", lazy=True)
    




    def __init__(self, creator,customer_id,vat_file_name=None, vat_file_path=None, days_until_due=None, notes=None, client_lpo_number=None):

        """
        Initialize an Invoice: It expects either Admin or Staff instance for 'creator'

        :param creator: Either an Admin or Staff instance created the invoice

        :param days_until_due: optional, customize the number of days until the invoice is due. 
        """
        # # Query to determine if the creator is an Admin or Staff
        # creator = Admin.query.get(creator_id) or Staff.query.get(creator_id)

        if isinstance(creator, Admin):
            self.admin_id = creator.id
            self.staff_id = 0

        elif isinstance(creator, Staff):
            self.staff_id = creator.id
            self.admin_id=0

        else:
            raise ValueError("Creator must be an Admin or Staff")

        if days_until_due is not None:
            self.days_until_due = days_until_due
        self.date_created = datetime.today().date()
        self.due_date = self.date_created + timedelta(days=self.days_until_due)
        self.invoice_number = Invoice.generate_invoice_number()
        self.vat_file_name = vat_file_name
        self.vat_file_path = vat_file_path
        self.total_amount = self.calculate_total_amount()
        self.balance = self.total_amount
        self.customer_id = customer_id
        self.notes =notes
        self.client_lpo_number = client_lpo_number
    
    
    #Apply table constraint to the column that fills if its either Admin or Staff who created a specific Invoice
    __table_args__ =(
        db.CheckConstraint(
            "admin_id IS NOT NULL OR staff_id IS NOT NULL", name= "check_admin_or_staff"
        ),
    )

    #serialize 
    serialize_only = ("invoice_number", "date_created", "days_until_due", "due_date")

    #Because this is tied to a class not a single instance
    @classmethod
    def generate_invoice_number(cls):
        """
        Purpose: function that will auto increment the invoice_number
        """

        last_invoice = Invoice.query.order_by(cls.id.desc()).first()

        if last_invoice:
            return last_invoice.invoice_number + 1
        return 700000

    # retrieve the total_amount from Item class
    def calculate_total_amount(self):
        total = sum(item.total for item in self.items)
        return total
    
    #We need to update the balance when payments are made
    def update_balance(self, payment_amount):
        if payment_amount > 0:
            self.balance -= payment_amount
        else:
            raise ValueError("The amount must be more than 0")            
        if self.balance < 0:
            self.balance = 0.0


    # Call this after adding items or when creating the invoice
    def update_total_amount(self):
        self.total_amount = self.calculate_total_amount()
        self.balance = self.total_amount



#Purchase 
class Purchase(db. Model, SerializerMixin):

    __tablename__ = "purchases"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    purchase_number = db.Column(db.Integer(), nullable=False, default=2000)
    invoice_number = db.Column(db.String(), nullable=True)
    date_purchased = db.Column(db.Date, nullable=False, default=db.func.current_timestamp())
    date_due = db.Column(db.Date, nullable=False)
    delivered_by = db.Column(db.String(), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)


    #Serialize
    serialize_only =("purchase_number", "date_purchased", "date_due", "delivery_date", "delivered_by")

    #Foreign Key    
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=False)
    lpo_id = db.Column(db.Integer(), db.ForeignKey("lpos.id"), nullable=True)
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)

    #Initialization
    def __init__(self, date_purchased, date_due, delivered_by, delivery_date, instance, invoice_number, vendor_id, lpo_id):
        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance,Staff):
            self.staff_id = instance.id
            self.admin_id = 0

        self.date_purchased = date_purchased
        self.date_due = date_due
        self.delivered_by = delivered_by
        self.delivery_date = delivery_date
        self.purchase_number = Purchase.increment_purchase_number()
        self.invoice_number = invoice_number
        self.vendor_id = vendor_id
        self.lpo_id = lpo_id
    
    
    # Increment Purchase number
    @classmethod
    def increment_purchase_number(cls):
        new_purchase = Purchase.query.order_by(Purchase.purchase_number.desc()).first()
        if new_purchase:
            return new_purchase.purchase_number + 1
        return 2000
    

    #Relationship
    items =db.relationship("Item", backref="purchase", lazy=True)    
    lpos = db.relationship("Lpo", backref="purchase", lazy=True)
    invoices = db.relationship("Invoice", secondary=purchase_invoice, backref="purchase", lazy=True)
    payments = db.relationship("Payment", backref="purchase", lazy=True)
    
    def calculate_total_amount(self):
        """Calculates the total for all items in this purchase."""
        total = sum(item.total for item in self.items)
        return total
    
    # Call this after adding items or during purchase initialization
    def update_total_amount(self):
        self.total_amount = self.calculate_total_amount()



#Vat Enum
class VatEnum(enum.Enum):
    VAT_0 = 0
    VAT_2 = 0.02
    VAT_10 = 0.1
    VAT_16 = 0.16

#Item
class Item(db.Model, SerializerMixin):
    __tablename__ = "items"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    description = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    vat = db.Column(db.Float(), nullable=True)
    vat_percentage = db.Column(SQLEnum(VatEnum), default=VatEnum.VAT_16)
    discount = db.Column(db.Float(), nullable=True)
    total = db.Column(db.Float(), nullable=False)

    #serialize
    serialize_only = ('description', 'quantity', 'price', 'amount', 'vat', 'discount', 'total')

    #Foreign Key
    invoice_id = db.Column(db.Integer(), db.ForeignKey("invoices.id"), nullable=False)
    category_id = db.Column(db.Integer(), db.ForeignKey("categories.id"), nullable=False)
    serial_number_id = db.Column(db.Integer(), db.ForeignKey("serial_numbers.id"), nullable=False, unique=True)
    currency_id = db.Column(db.Integer(), db.ForeignKey("currencies.id"), nullable=False)
    purchase_id = db.Column(db.Integer(), db.ForeignKey("purchases.id"), nullable=False)
    lpo_id = db.Column(db.Integer(),db.ForeignKey("lpos.id"))
    quotation_id =db.Column(db.Integer(), db.ForeignKey("quotations.id"), nullable=False)




    #Relationship    


    #for different instances
    def __init__(self, category_id, description, serial_number_id, quantity, price, currency_id,invoice_id, quotation_id, purchase_id, lpo_id, discount=None, vat_percentage=VatEnum.VAT_16):

        self.vat_percentage= vat_percentage
        self.category_id = category_id
        self.description =description
        self.serial_number_id = serial_number_id
        self.quantity = quantity
        self.price = price
        self.amount =self.calculate_amount()        
        self.vat = self.calculate_vat(self.vat_percentage)
        self.total = self.calculate_total()
        self.currency_id = currency_id 
        self.discount = self.calculate_discount(discount) if discount else 0
        self.invoice_id = invoice_id
        self.quotation_id = quotation_id
        self.purchase_id = purchase_id
        self.lpo_id = lpo_id
        
    #calculate Amount
    def calculate_amount(self):
        return self.quantity * self.price

    #update VAT if changed after initialization
    def update_vat_percentage(self, new_vat_percentage:VatEnum):
        if not isinstance(new_vat_percentage, VatEnum):
            raise ValueError("new_vat_percentage must be an instance of VatEnum")
        self.vat_percentage = new_vat_percentage
        self.vat =self.calculate_vat(new_vat_percentage)
        self.total = self.calculate_total()

    #calculate vat
    def calculate_vat(self, vat_percentage):  
        vat_percentage_value = vat_percentage.value   
        return self.amount * vat_percentage_value if vat_percentage_value else 0
    
    #calculate the total amount
    def calculate_total(self):
        return self.amount + (self.vat or 0.0) - (self.discount or 0.0) 
    
    #Doscount calulation
    def calculate_discount(self, discount):
        given_discount = float(discount)
        return self.amount * given_discount if given_discount else 0
    
    #exchange rate change
    def update_currency(self, new_currency):        #The argument is the Currency instance
        exchange_rate = new_currency.exchange_rate  #Get the exchange rate
        if exchange_rate <= 0:
            raise ValueError("Exchange rate must be greater than zero")
        self.amount *= exchange_rate
        self.vat = self.calculate_vat(self.vat_percentage)
        self.total = self.amount + self.vat
        self.currency_id = new_currency.id


    #validate fields
    @validates("amount")
    def validate_amount(self, key, value):
        if value < 0:
            raise ValueError("Amount can't be negative")
        return value
    
    @validates("vat")
    def validate_vat(self, key, value):
        if value < 0:
            raise ValueError("VAT can't be negative")
        return value

    @validates("total")
    def validate_total(self, key, value):
        if value < 0:
            raise ValueError("Total can't be negative")
        return value

    @validates("vat_percentage")
    def validate_vat_percentage(self, key, value):
        vat_percentage_value = float(value.value)
        if not (0 <= vat_percentage_value <= 1):
            raise ValueError("VAT percentage must be between 0 and 1")
        return value

    @validates("discount")
    def validate_discount(self, key, value):
        if value is not None and value < 0:
            raise ValueError("Discount can never be a negative")
        if value and value > self.amount:
            raise ValueError("Discount can never be more than the amount")
        return value

#Category
class Category(db.Model, SerializerMixin):
    __tablename__ = "categories"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    name = db.Column(db.String(), nullable=False)

    #serialize
    serialize_only= ("name",)

    #ForeignKey
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)    
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)

    #Relationship
    items = db.relationship("Item", backref="category", lazy=True)

    #initialize
    def __init__(self, instance, name):
        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance, Staff):
            self.staff_id = instance.id
            self.admin_id = 0
        else:
            raise ValueError("Only Admin or Staff allowed to create a category")       
        self.name = name     



#Serial numbers for each product
class SerialNumber(db.Model, SerializerMixin):
    __tablename__ = "serial_numbers"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    serial = db.Column(db.String(), nullable=False, unique=True, index=True)

    #serialize
    serialize_only = ("serial",)

    #relationship
    item = db.relationship("Item", backref="serial_number", uselist=False, lazy=True)


#Currency
class Currency(db.Model, SerializerMixin):
    __tablename__ = "currencies"

    id = db.Column(db.Integer(), primary_key=True, unique=True)
    name = db.Column(SQLEnum(CurrencyEnum), nullable=False, default = CurrencyEnum.KSHS)
    symbol = db.Column(db.String(), nullable=False, unique=True)
    exchange_rate = db.Column(db.Float(), nullable=False, default=0)

    #serialize
    serialize_only =("name", "symbol", "exchange_rate")

    #Relationship
    items = db.relationship("Item", backref="currency", lazy=True)

#LPO
class Lpo(db.Model, SerializerMixin):
    __tablename__ = "lpos"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    lpo_number = db.Column(db.Integer(), nullable=False, unique=True)
    date_issued = db.Column(db.Date, default=db.func.current_date())
    days_until_due = db.Column(db.Integer(), default=30)
    date_due = db.Column(db.Date(), server_default=db.func.date(db.func.current_date(), "+30 days"))

    #serialize
    serialize_only =("lpo_number", "date_issued", "days_until_due", "date_due")

    #Foreign Key
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=False)
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)


    #Relationship
    items = db.relationship("Item", backref="lpo", lazy=True)

    #Initialization
    def __init__(self,instance, vendor_id, date_due=None,days_until_due=None):
        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance, Staff):
            self.staff_id = instance.id
            self.admin_id = 0
        else:
            raise ValueError("Must be an Admin or Staff")

        #Lpo number set
        self.lpo_number = Lpo.lpo_number_increment()  
        self.vendor_id = vendor_id      
        
        #Handling due date logic
        self.days_until_due=days_until_due if days_until_due else 30
        self.date_issued = db.func.current_date()
        if date_due:
            self.date_due = date_due
        else:
            self.date_due = db.func.date(self.date_issued, f"+{self.days_until_due} days")
            
        

    #Function to auto increment LPO number
    @classmethod
    def lpo_number_increment(cls):
        last_lpo_number = Lpo.query.order_by(cls.lpo_number.desc()).first()
        if last_lpo_number:
            return last_lpo_number.lpo_number + 1
        return 3000

# PaymentModeEnum 
class PaymentModeEnum(enum.Enum):
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
    payment_mode = db.Column(SQLEnum(PaymentModeEnum), nullable=False)
    date_paid = db.Column(db.Date(), default= db.func.current_date())
    amount = db.Column(db.Float(), nullable=False)
    payment_reference = db.Column(db.String(), nullable=True)    

    #serialize
    serialize_only = ("payment_mode", "date_paid", "payment_reference")


    #Foreign Key
    invoice_id = db.Column(db.Integer(), db.ForeignKey("invoices.id"), nullable=True)
    purchase_id = db.Column(db.Integer(), db.ForeignKey("purchases.id"), nullable=True)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    vendor_id = db.Column(db.Integer(), db.ForeignKey("vendors.id"), nullable=True)
    customer_id = db.Column(db.Integer(), db.ForeignKey("customers.id"), nullable=True)


    # Validation to ensure either invoice or purchase is provided
    @validates('invoice_id', 'purchase_id')
    def validate_invoice_or_purchase(self, key, value):
        if key == 'invoice_id' and not value and not self.purchase_id:
            raise ValueError("Payment must be linked to either an invoice or a purchase.")
        if key == 'purchase_id' and not value and not self.invoice_id:
            raise ValueError("Payment must be linked to either an invoice or a purchase.")
        return value


    #Relationship
    # items = db.relationship("Item", secondary=payment_items, backref="payments", nullable=False, lazy=True)

    #Initialization
    def __init__(self, instance,payment_mode, amount, customer_id=None, vendor_id= None, invoice_id=None, purchase_id = None, payment_reference=None):
        
        """
    Initialize Payment: It expects either Admin or Staff instance for 'instance'
    
    :param instance: Either an Admin or Staff instance made the payment
    :param payment_mode: Mode of payment (cash, mpesa, etc.)
    :param amount: Amount paid
    :param invoice_id: Optional invoice linked to the payment
    :param purchase_id: Optional purchase linked to the payment
    :param payment_reference: Optional payment reference number (like a transaction ID)
    """
        if not invoice_id and not purchase_id:
            raise ValueError("Payment must be linked to either an invoice or a purchase.") 

        if invoice_id:
            self.invoice_id = invoice_id   
        elif purchase_id:
            self.purchase_id = purchase_id   


        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0

        elif isinstance(instance, Staff)            :
            self.staff_id = instance.id
            self.admin_id = 0

        else:
            raise ValueError("Payment can only be made by Admin or Staff")
        
        #Initialize payment mode and optional reference
        if isinstance(payment_mode, PaymentModeEnum):
            self.payment_mode = payment_mode

        self.payment_reference = payment_reference
        self.amount = amount
        self.vendor_id = vendor_id
        self.customer_id = customer_id



# Quotation
class Quotation(db.Model, SerializerMixin):
    __tablename__ = "quotations"

    id = db.Column(db.Integer(), primary_key=True, nullable=False)
    quotation_number = db.Column(db.Integer(), nullable=False, unique=True)
    quotation_date = db.Column(db.Date(), default= db.func.current_date())
    quotation_days = db.Column(db.Integer(), default=30)
    quotation_due = db.Column(db.Date(), server_default=db.func.date(db.func.current_date(), "+30 days"))

    # serialization
    serialize_only= ("quotation_number", "quotation_date", "quotation_due")

    #Foreign Key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)
    

    #Relationship
    items = db.relationship("Item", backref="quotation", lazy=True)


    #initialization
    def __init__(self,instance, quotation_days=None):
        """
        Initialize quotation: It expects either Admin or Staff instance for 'instance'

        :param instance: Either an Admin or Staff instance created the quotation

        :param quotation_days: optional, customize the number of days until the quotation is due. 
        """

        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0

        elif isinstance(instance, Staff):
            self.staff_id = instance.id
            self.admin_id = 0

        else:
            raise ValueError("Creator must be an Admin or Staff")

        if quotation_days is not None:
            self.quotation_days = quotation_days
            self.quotation_due = db.func.date(self.quotation_date, f"+{self.quotation_days} days")

        self.quotation_number = Quotation.quotation_increment()


    #quotation auto-increment
    @classmethod
    def quotation_increment(cls):
        last_quotation_number = Quotation.query.order_by(cls.quotation_number.desc()).first()
        if last_quotation_number:
            return last_quotation_number.quotation_number + 1

        return 700000


# Delivery note
class DeliveryNote(db.Model, SerializerMixin):
    __tablename__ = "deliverynotes"

    id = db.Column(db.Integer(), primary_key=True)
    delivery_number = db.Column(db.Integer(), nullable=False, unique=True)
    delivery_date = db.Column(db.Date(), nullable=False, default=db.func.current_date())
    delivery_file_name = db.Column(db.String(), nullable=True)
    delivery_file_path = db.Column(db.String(), nullable=True)

    #Serialize
    serialize_only = ("delivery_date", "delivery_number")

    #Foreign Key
    invoice_id = db.Column(db.Integer(), db.ForeignKey("invoices.id"), nullable=False)
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)

    #Relationship
    

    #initialization
    def __init__(self, instance, invoice_id, delivery_file_name=None, delivery_file_path=None):
        self.invoice_id = invoice_id

        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance, Staff)            :
            self.staff_id = instance.id
            self.admin_id = 0
        else:
            raise ValueError("Can only be create by an Admin or Staff")
        
        self.delivery_number = DeliveryNote.increment_delivery_number()
        self.delivery_file_name = delivery_file_name
        self.delivery_file_path = delivery_file_path
        

    # To auto increment delivery_number
    @classmethod
    def increment_delivery_number(cls):
        last_delivery_number = DeliveryNote.query.order_by(cls.delivery_number.desc()).first()
        if last_delivery_number:
            return last_delivery_number.delivery_number + 1
        return 700000


# Enum class
class JobCardStatus(enum.Enum):
    COMPLETED= "completed"
    IN_PROGRESS = "in_progress"
    CANCELED = "canceled"

# Job card
class JobCard(db.Model, SerializerMixin):
    __tablename__ = "jobcards"

    id = db.Column(db.Integer(), primary_key=True)
    job_card_number = db.Column(db.Integer(), nullable=False, unique=True)
    job_card_date = db.Column(db.Date(), default = db.func.current_date())
    job_card_status = db.Column(SQLEnum(JobCardStatus), nullable=False, default=JobCardStatus.IN_PROGRESS)
    description = db.Column(db.String(), nullable=False)
    quantity = db.Column(db.Integer(), nullable=False)

    #Foreign Key
    admin_id = db.Column(db.Integer(), db.ForeignKey("admins.id"), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey("staffs.id"), nullable=False)

    #relationship
    invoice = db.relationship("Invoice", secondary=jobcard_invoice, backref="jobcards", lazy=True)
    

    #Initialization
    def __init__(self, instance, job_card_status,description, quantity,invoice_id=None):
        if invoice_id is not None:
            invoice = Invoice.query.get(invoice_id)
            if invoice:
                self.invoice.append(invoice)
        if isinstance(instance, Admin):
            self.admin_id = instance.id
            self.staff_id = 0
        elif isinstance(instance, Staff):
            self.staff_id = instance.id
            self.admin_id = 0
        self.job_card_number = JobCard.auto_increment_job_card_number()
        self.job_card_status = job_card_status
        self.description = description
        self.quantity = quantity


    #Auto-increment job_car_number
    @classmethod
    def auto_increment_job_card_number(cls):
        last_job_card_number = JobCard.query.order_by(cls.job_card_number.desc()).first()
        if last_job_card_number:
            return last_job_card_number.job_card_number + 1
        else:
            return 1300


