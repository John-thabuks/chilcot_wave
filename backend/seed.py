from config import app, db
from models import Users, Admin, Staff, Customer, Vendor, Invoice, Purchase, Item, Category, SerialNumber, Currency, Lpo, Payment, Quotation, DeliveryNote, JobCard, DepartmentEnum, EmploymentStatusEnum, CurrencyEnum, VatEnum, PaymentModeEnum


from faker import Faker
import uuid



fake = Faker()
import random
import string
from datetime import datetime, timedelta


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





    #------> Admin: We shall have just one Admin
    admin = Admin(
        first_name ="John", 
        last_name="Thabuks", 
        username="admin", 
        email="thabuks.john@gmail.com", password="@Password1234"
        )
    
    db.session.add(admin)
    db.session.commit()
    print(f"{admin} data inserted successfully!")





    #------> Satff: I want 5 staff members
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





    #----> Customer
    customer_members = []

    #Generate kra_pin
    def generate_kra_pin():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    

    for _ in range(5):

        #randomly who created customer admin or staff_member
        creator = random.choice([admin] + customer_members)

        customer = Customer(
            name= fake.name(),
            email = fake.email(),
            phone= ''.join(filter(str.isdigit, fake.phone_number())),
            kra_pin= generate_kra_pin(),
            location= fake.address(),
            country=fake.country(),
            currency = CurrencyEnum.KSHS,
            date_enrolled = fake.date_between(start_date='-5y', end_date='-1y'),
            date_last_updated = fake.date_between(start_date='-1y', end_date='today'),
            active= True,
            account_limit= random.randint(100_000, 3_000_000),
            instance = creator
        )
        customer_members.append(customer)
        db.session.add(customer)

    db.session.commit()
    print(f"{len(staff_members)} data inserted successfully!")




    #----> Vendor: created by either admin or staff_members. We need 5 venodrs
    vender_members = []
    vender_ids = []


    for _ in range(5):

        #Random creator:
        creator = random.choice([admin] + staff_members)

        vendor = Vendor(
            name = fake.name(),
            email= fake.email(),
            phone= "".join(filter(str.isdigit, fake.phone_number())),
            kra_pin= generate_kra_pin(),
            location=fake.address(),
            country=fake.country(),
            currency=CurrencyEnum.KSHS,
            date_registered= fake.date_between(start_date="-4y", end_date="-1y"),
            active=True, 
            instance = creator.id
        )
        db.session.add(vendor)
        db.session.flush()
        vender_members.append(vendor)
        vender_ids.append(vendor.id)

    db.session.commit()
    print(f"{len(vender_members)} data inserted successfully!")




    #----> Invoice
    invoices_id = []
    
    
    #setting up the start_date and end_date
    end_date = datetime.today()
    start_date = end_date - timedelta(days=60)

    for _ in range(10):

        #We want a random customer
        rand_customer = random.choice(customer_members)

        creator = random.choice([admin] + staff_members)        

        # Random invoice creation date
        date_created = fake.date_between(start_date=start_date, end_date=end_date)

        # Calculating due date from date_created
        days_until_due = random.randint(5, 60)
        due_date = date_created + timedelta(days=days_until_due)

        invoice = Invoice(
        customer_id = rand_customer.name,
        invoice_number = Invoice.auto_increment(),
        date_created = date_created,
        days_until_due = days_until_due,
        due_date = due_date,
        notes = fake.sentence(),
        client_lpo_number = generate_kra_pin(),        
        vat_file_name = fake.file_name(),
        vat_file_path = fake.file_path(),
        creator= creator.id
        )

        db.session.add(invoice)
        db.session.flush()
        invoice.update_total_amount()
        invoices_id.append(invoice.id)

    db.session.commit()
    print(f"{len(invoices_id)} invoices created successfully!")
    


    #----> Category
    category_id = []

    for _ in range(5):
        category = Category(
            name = fake.word(),
            instance = random.choice([admin] + staff_members)
        )

        db.session.add(category)
        db.session.flush()
        category_id.append(category.id)

    db.session.commit()
    print(f"{len(category_id)} invoices created successfully!")



    # ----> Serial_number
    serial_number_ids = []

    #generate fake serial numbers
    def fake_serials():
        letters = fake.random_uppercase_letter() + fake.random_uppercase_letter()
        digits = str(fake.random_number(digits=5, fix_len=True))
        fake_serial = letters + digits
        return fake_serial

    for _ in range(5):
        serial_num = SerialNumber(
            serial = fake_serials()
        )

        db.session.add(serial_num)
        db.session.flush()
        serial_number_ids.append(serial_num.id)

    db.session.commit()
    print(f"{len(serial_number_ids)} serial numbers created successfully!")



    # ----> Currency
    currency_ids = []

    for _ in range(4):
        currency = Currency(
            name = fake.currency_name(),
            symbol = fake.currency_symbol(),
            exchange_rate = round(random.uniform(100, 200),2)
        )

        db.session.add(currency)
        db.session.flush()
        currency_ids.append(currency.id)

    db.session.commit()
    print(f"{len(currency_ids)} currencies created successfully!")




    # ----> Lpo
    lpo_ids = []

    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)

    for _ in range(5):

        date_issued = fake.date_between(start_date=start_date, end_date=end_date)
        days_until_due = random.randint(5, 30)
        date_due = date_issued + timedelta(days=days_until_due)

        lpo = Lpo(
            lpo_number = Lpo.lpo_number_increment(),
            date_issued = date_issued,
            days_until_due = days_until_due,
            date_due = date_due,
            vendor_id = random.choice(vender_members),
            instance = random.choice([admin] + staff_members)
        )

        db.session.add(lpo)
        db.session.flush()
        lpo_ids.append(lpo.id)

    db.session.commit()
    print(f"{len(lpo_ids)} LPOs created successfully!")




    # ----> Quotation
    quotation_ids = []

    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)

    for _ in range(5):

        quotation_date = fake.date_between(start_date=start_date, end_date=end_date)
        quotation_days = random.randint(30)
        quotation_due = quotation_date + timedelta(days=quotation_days)

        quotation = Quotation(
            quotation_number = Quotation.quotation_increment(),
            quotation_date = quotation_date,
            quotation_days = quotation_days,
            quotation_due = quotation_due,
            instance = random.choice([admin] + staff_members)
        )

        db.session.add(quotation)
        db.session.flush()
        quotation_ids.append(quotation.id)
    
    db.session.commit()
    print(f"{len(quotation_ids)} Quotations created successfully!")



    # ----> Purchase
    purchase_ids = []

    end_date= datetime.today()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(5):

        date_created = fake.date_between(start_date=start_date, end_date=end_date)

        # Calculating due date from date_created
        days_until_due = random.randint(5, 30)
        due_date = date_created + timedelta(days=days_until_due)


        purchase = Purchase(
            purchase_number= Purchase.increment_purchase_number(),
            invoice_number = random.choice(invoices_id),
            date_purchased = date_created,
            date_due = due_date,
            delivered_by = fake.full_name(),
            delivery_date = date_created,
            instance = random.choice([admin] + staff_members),
            vendor_id = random.choice(vender_members),
            lpo_id = random.choice(lpo_ids),            
        )

        db.session.add(purchase)
        db.session.flush()
        purchase.update_total_amount()
        purchase_ids.append(purchase.id)

    db.session.commit()
    print(f"{len(purchase_ids)} Purchases created successfully!")




    #----> Item
    all_items = []
    for _ in range(5):
        
        item = Item(
            description = fake.sentence(),
            quantity = random.randint(1,50),
            price = round(random.uniform(1000, 50000),2),
            invoice_id = random.choice(invoices_id),
            category_id = random.choice(category_id),
            serial_number_id= random.choice(serial_number_ids),
            currency_id = random.choice(currency_ids),
            purchase_id = random.choice(purchase_ids),
            lpo_id = random.choice(lpo_ids),
            quotation_id = random.choice(quotation_ids),
            vat_percentage = VatEnum.VAT_16
        )
        db.session.add(item)
        db.session.flush()
        all_items.append(item.id)

    db.session.commit()
    print(f"{len(all_items)} Items created successfully!")


    
    # ----> Payment
    payment_id = []
    payments = []

    end_date = datetime.today()
    start_date = end_date - timedelta(days=180)

    for _ in range(15):

        payment = Payment(
            payment_mode = random.choice(list(PaymentModeEnum)),
            date_paid = fake.date_between(start_date=start_date, end_date=end_date),
            amount = round(random.uniform(100, 30000),2),
            payment_reference = str(uuid.uuid4()),   #output: f9b8a67e-d3a7-40d4-83f3-e29f45d9db56
            invoice_id = random.choice(invoices_id),
            purchase_id = random.choice(purchase_ids),
            vendor_id = random.choice(vender_ids),
            customer_id = random.choice(customer_members),
            instance = random.choice([admin] + staff_members)
        )

        db.session.add(payment)
        db.session.flush()
        payment_id.append(payment.id)
        payments.append(payment)

    db.session.commit()
    print(f"{len(payment_id)} Payments created successfully!")








