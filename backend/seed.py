from config import app, db
from models import Users, Admin, Staff, Customer, Vendor, Invoice, Purchase, Item, Category, SerialNumber, Currency, Lpo, Payment, Quotation, DeliveryNote, JobCard, DepartmentEnum, EmploymentStatusEnum, CurrencyEnum, VatEnum, PaymentModeEnum, JobCardStatus


from faker import Faker
import uuid



fake = Faker()
import random
import string
from datetime import datetime, timedelta
import json

from sqlalchemy import exists


with app.app_context():
    
    #Before starting: Lets delete previous data
    Admin.query.delete()
    Staff.query.delete()
    Users.query.delete()
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
    admin_id =[]
    admin_obj = []
    admin = Admin(
        first_name ="John", 
        last_name="Thabuks", 
        username="admin", 
        email="thabuks.john@gmail.com", password="@Password1234",        
        )
    
    # The permissions_dict property automatically converts the permissions to JSON
    admin.permissions_dict = {
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

    
    db.session.add(admin)
    db.session.flush()
    admin_id.append(admin.id)
    admin_obj.append(admin)
    db.session.commit()
    print(f"{admin} data inserted successfully!")





    #------> Satff: I want 5 staff members
    staff_members = []
    staff_members_id =[]
    
    for _ in range(5):
        username = fake.user_name()
        if len(username) <=3:
            username += "@123"

        staff = Staff(
            first_name = fake.first_name(),
            last_name = fake.last_name(),
            username = username,
            email = fake.email(),
            password= "@Password1234",
            date_employed= fake.date_between(start_date="-7y", end_date="-1y"),
            department = random.choice(list(DepartmentEnum)), 
            employment_status = EmploymentStatusEnum.ONGOING,
            date_exited = None,
            admin_id = admin.id
        )

        # Assign permissions for staff via permissions_dict property
        staff.permissions_dict = {
        'vendor': ['C', 'R', 'U'],  # Staff can only Create, Read, Update vendors
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

        db.session.add(staff)
        db.session.flush()
        staff_members_id.append(staff.id)
        staff_members.append(staff)
    db.session.commit()
    print(f"{len(staff_members)} staff data inserted successfully!")





    #----> Customer
    customer_members = []
    customer_members_ids = []

    #Generate kra_pin
    def generate_kra_pin():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    
    username = fake.user_name()
    if len(username) <=3:
        username += "@123"

    for _ in range(5):

        #randomly who created customer admin or staff_member
        creator = random.choice(admin_obj + staff_members)

        customer = Customer(
            name=fake.first_name(),
            email = fake.email(),
            password= "@Password1234",
            phone= ''.join(filter(str.isdigit, fake.phone_number())),
            kra_pin= generate_kra_pin(),
            location= fake.address(),
            country=fake.country(),            
            date_enrolled = fake.date_between(start_date='-5y', end_date='-1y'),
            date_last_updated = fake.date_between(start_date='-1y', end_date='today'),
            active= True,
            account_limit= random.randint(100_000, 3_000_000),
            instance = creator,
            
        )

        # Assign permissions for staff via permissions_dict property
        staff.permissions_dict = {
            'invoice': ['R'],
            'delivery': ['R']
        }
        
        db.session.add(customer)        
        db.session.flush()
        customer_members_ids.append(customer.id)
        customer_members.append(customer)

    db.session.commit()
    print(f"{len(staff_members)} data inserted successfully!")




    #----> Vendor: created by either admin or staff_members. We need 5 venodrs
    vender_members = []
    vender_ids = []


    for _ in range(5):

        #Random creator:
        creator = random.choice(admin_obj + staff_members)

        vendor = Vendor(
            name = fake.name(),
            email= fake.email(),
            phone= "".join(filter(str.isdigit, fake.phone_number())),
            kra_pin= generate_kra_pin(),
            location=fake.address(),
            country=fake.country(),
            currency=CurrencyEnum.KSHS,
            # date_registered= fake.date_between(start_date="-4y", end_date="-1y"),
            # active=True, 
            instance = creator
        )
        db.session.add(vendor)
        db.session.flush()
        vender_members.append(vendor)
        vender_ids.append(vendor.id)

    db.session.commit()
    print(f"{len(vender_members)} data inserted successfully!")




    #----> Invoice
    invoices_id = []
    
    #Query Customer
    customers = Customer.query.all()
    
    for customer in customers:
    
        #setting up the start_date and end_date
        end_date = datetime.today()
        start_date = end_date - timedelta(days=60)

        for _ in range(random.randint(1,5)):

        
            creator = random.choice(admin_obj + staff_members)        

            # Random invoice creation date
            date_created = fake.date_between(start_date=start_date, end_date=end_date)

            # Calculating due date from date_created
            days_until_due = random.randint(5, 60)
            due_date = date_created + timedelta(days=days_until_due)

            invoice = Invoice(
            customer_id = customer.id,                        
            days_until_due = days_until_due,            
            notes = fake.sentence(),
            client_lpo_number = generate_kra_pin(),        
            vat_file_name = fake.file_name(),
            vat_file_path = fake.file_path(),
            creator= creator
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
            instance = random.choice(admin_obj + staff_members)
        )

        db.session.add(category)
        db.session.flush()
        category_id.append(category.id)

    db.session.commit()
    print(f"{len(category_id)} invoices created successfully!")



    # ----> Serial_number
    serial_number_ids = []


    for _ in range(100):
        serial_num = SerialNumber(
            serial = fake.unique.bothify(text='???-############')
        )

        db.session.add(serial_num)
        db.session.flush()
        serial_number_ids.append(serial_num.id)

    db.session.commit()
    print(f"{len(serial_number_ids)} serial numbers created successfully!")



    # ----> Currency
    currency_ids = []

    for currency_enum in CurrencyEnum:
    
        currency = Currency(
            name = currency_enum.name,
            symbol = currency_enum.value,
            exchange_rate = round(random.uniform(100, 200),2)
        )

        db.session.add(currency)
        db.session.flush()
        currency_ids.append(currency.id)

    db.session.commit()
    print(f"{len(currency_ids)} currencies created successfully!")




    # ----> Lpo
    lpo_ids = []

    vendors = Vendor.query.all()

    for vendor in vendors:

        creator = random.choice(admin_obj + staff_members)

        end_date = datetime.today().now()
        start_date = end_date - timedelta(days=30)

        date_issued = fake.date_between(start_date=start_date, end_date=end_date)
        days_until_due = random.randint(5, 30)
        date_due = date_issued + timedelta(days=days_until_due)

        for _ in range(random.randint(1,3)):
            lpo = Lpo(                        
            days_until_due = days_until_due,            
            vendor_id = vendor.id,
            instance = creator,
            date_due = date_due
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

        creator = random.choice(admin_obj + staff_members)

        quotation_date = fake.date_between(start_date=start_date, end_date=end_date)
        quotation_days = random.randint(5, 30)
        quotation_due = quotation_date + timedelta(days=quotation_days)

        quotation = Quotation(                        
            quotation_days = quotation_days,            
            instance = creator
        )

        db.session.add(quotation)
        db.session.flush()
        quotation_ids.append(quotation.id)
    
    db.session.commit()
    print(f"{len(quotation_ids)} Quotations created successfully!")



    # ----> Purchase
    purchase_ids = []

    vendors = Vendor.query.all()

    for vendor in vendors:

        lpo = random.choice(lpo_ids)

        end_date= datetime.today()
        start_date = end_date - timedelta(days=30)
        creator =random.choice(admin_obj + staff_members)
    
        for _ in range(random.randint(1,5)):

            date_created = fake.date_between(start_date=start_date, end_date=end_date)

            # Calculating due date from date_created
            days_until_due = random.randint(5, 30)
            due_date = date_created + timedelta(days=days_until_due)


            purchase = Purchase(            
            invoice_number = random.choice(invoices_id),
            date_purchased = date_created,
            date_due = due_date,
            delivered_by = fake.first_name(),
            delivery_date = date_created,
            instance = creator,
            vendor_id = vendor.id,
            lpo_id = lpo,            
            )

            db.session.add(purchase)
            db.session.flush()
            purchase.update_total_amount()
            purchase_ids.append(purchase.id)

    db.session.commit()
    print(f"{len(purchase_ids)} Purchases created successfully!")




    #----> Item
    all_items = []

    invoices = Invoice.query.all()

    for invoice in invoices:

        purchase = random.choice(purchase_ids)
        quotation = random.choice(quotation_ids)
        

        for _ in range(random.randint(1,5)):
            if not serial_number_ids:
                print("No more unique serial numbers available!")
                break

            serial_number_id = serial_number_ids.pop(0)
        
            item = Item(
            description = fake.sentence(),
            quantity = random.randint(1,50),
            price = round(random.uniform(1000, 50000),2),
            invoice_id = invoice.id,
            category_id = random.choice(category_id),
            serial_number_id= serial_number_id,
            currency_id = random.choice(currency_ids),
            purchase_id = purchase,
            lpo_id = random.choice(lpo_ids),
            quotation_id = quotation,
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

        # Randomly pick a vendor, customer, invoice, and purchase
        vendor = random.choice(vender_ids) if vender_ids else None
        customer = random.choice(customer_members_ids) if customer_members_ids else None    
        invoice = random.choice(invoices_id) if invoices_id else None
        purchase = random.choice(purchase_ids) if purchase_ids else None
        creator = random.choice(admin_obj + staff_members)

        if random.choice([True, False]) and invoice:  # Ensure invoice exists
            payment = Payment(
                instance = creator,
                payment_mode= random.choice(list(PaymentModeEnum)),
                amount= round(random.randint(1000, 20000),2),                
                customer_id= customer,
                invoice_id= invoice,
                payment_reference= fake.uuid4()
                )

        elif purchase:  # Ensure purchase exists
            payment = Payment(
                instance = creator,
                payment_mode= random.choice(list(PaymentModeEnum)),
                amount= round(random.randint(1000, 20000), 2),
                vendor_id= vendor,
                purchase_id= purchase,  # Only create if purchase is not None
                payment_reference= fake.uuid4()
            )
        else:
            print("Skipping creation of payment due to missing invoice and purchase.")

        if invoice or purchase:
            db.session.add(payment)
            db.session.flush()
            payment_id.append(payment.id)
            payments.append(payment)

    db.session.commit()
    print(f"{len(payment_id)} Payments created successfully!")


    # DeliveryNote
    deliver_notes = []
    delivery_note_id = []

    for _ in range(10):
        invoice_id = random.choice(invoices_id)
        creator = random.choice(admin_obj + staff_members)

        d_note = DeliveryNote(                        
            delivery_file_name = fake.file_name(),
            delivery_file_path = fake.file_path(),
            invoice_id= invoice_id,
            instance = creator
        )

        db.session.add(d_note)
        db.session.flush()
        delivery_note_id.append(d_note.id)
        deliver_notes.append(d_note)

    db.session.commit()
    print(f"{len(delivery_note_id)} Delivery Notes created successfully!")




    #JobCard
    job_card_list = []
    job_card_id = []

    for _ in range(5):
        creator = random.choice(admin_obj + staff_members)
        jobcard = JobCard(                        
            job_card_status = random.choice(list(JobCardStatus)),
            description = fake.sentence(),
            quantity = random.randint(1, 10),
            instance = creator
        )
        db.session.add(jobcard)
        db.session.flush()
        job_card_list.append(jobcard)
        job_card_id.append(jobcard.id)

    db.session.commit()
    print(f"{len(job_card_id)} Delivery Notes created successfully!")


    # #association table: jobcard_invoice
    # invoice_id_list = [invoice.id for invoice in Invoice.query.all()]

    # job_card = JobCard.query.all()
    # for jobcard in job_card:
    #     selected_invoices = random.sample(invoice_id_list, random.randint(1,3))
    #     for invoice_id in selected_invoices:
    #         invoice_num = db.session.get(Invoice, invoice_id)
    #         jobcard.invoice.append(invoice_num)
    # db.session.commit()


    # #Association table: Purchase and Invoice
    # invoice_ids_collection = [invoice.id for invoice in Invoice.query.all()]

    # purchase_obj = Purchase.query.all()
    # for purchase in purchase_obj:
    #     invoice_collection = random.sample(invoice_ids_collection, random.randint(1,3))

    #     for each_invoice_id in invoice_collection:
    #         invoice = Invoice.query.get(each_invoice_id)
    #         purchase.invoices.append(invoice)

    # db.session.commit()



    # Association table: jobcard_invoice
    invoice_id_list = [invoice.id for invoice in Invoice.query.all()]
    job_card = JobCard.query.all()

    for jobcard in job_card:
        selected_invoices = random.sample(invoice_id_list, random.randint(1, 3))

        for invoice_id in selected_invoices:
            # Check if this combination already exists
            exists_query = db.session.query(
                db.session.query(JobCard)
                .filter(JobCard.id == jobcard.id)
                .filter(JobCard.invoices.any(id=invoice_id))
                .exists()
            ).scalar()

            # Only append if the association doesn't exist
            if not exists_query:
                invoice_num = db.session.get(Invoice, invoice_id)  # Use Session.get() instead of Query.get()
                jobcard.invoice.append(invoice_num)

    db.session.commit()

    # Association table: Purchase and Invoice
    invoice_ids_collection = [invoice.id for invoice in Invoice.query.all()]
    purchase_obj = Purchase.query.all()

    for purchase in purchase_obj:
        invoice_collection = random.sample(invoice_ids_collection, random.randint(1, 3))

        for each_invoice_id in invoice_collection:
            # Check if this combination already exists
            exists_query = db.session.query(
                db.session.query(Purchase)
                .filter(Purchase.id == purchase.id)
                .filter(Purchase.invoices.any(id=each_invoice_id))
                .exists()
            ).scalar()

            # Only append if the association doesn't exist
            if not exists_query:
                invoice = db.session.get(Invoice, each_invoice_id)  # Use Session.get() instead of Query.get()
                purchase.invoices.append(invoice)

    db.session.commit()





