from config import app, db
from models import Users, Admin, Staff, Customer, Vendor, Invoice, Purchase, Item, Category, SerialNumber, Currency, Lpo, Payment, Quotation, DeliveryNote, JobCard, DepartmentEnum, EmploymentStatusEnum
from faker import Faker



fake = Faker()
import random


with app.app_context():
    
    #Before starting: Lets delete previous data
    Users.query.delete()
    Admin.query.delete()
    Staff.query.delete()
    Customer.query.delete()
    Vendor.query.delete()
    Invoice.query.delete()
    Purchase.query.delete()
    Item.query.delete()
    Category.query.delete()
    SerialNumber.query.delete()
    Currency.query.delete()
    Lpo.query.delete()
    Payment.query.delete()
    Quotation.query.delete()
    DeliveryNote.query.delete()
    JobCard.query.delete()


    #Admin: We shall have just one Admin
    admin = Admin(
        first_name ="John", 
        last_name="Thabuks", 
        username="admin", 
        email="thabuks.john@gmail.com", password="@Password1234"
        )
    
    db.session.add(admin)
    db.session.commit()
    print(f"{admin} data inserted successfully!")

    #Satff: I want 5 staff members
    staff_members = []
    for _ in range(5):
        staff = Staff(
            first_name = fake.first_name(),
            last_name = fake.last_name(),
            username = fake.user_name(),
            email = fake.email(),
            password= "@Password1234",
            date_employed= fake.date_between(start_date="-7y", end_date="-1y"),
            department = random.choice(list(DepartmentEnum)), 
            employment_status = EmploymentStatusEnum.ONGOING,
            date_exited = None,
            admin_id = admin.id
        )
        staff_members.append(staff)
        db.session.add(staff)
    db.session.commit()
    print(f"{staff_members} data inserted successfully!")




