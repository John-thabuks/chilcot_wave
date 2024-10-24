from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard, DepartmentEnum, EmploymentStatusEnum
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask import request, jsonify
from datetime import datetime, timedelta
from sqlalchemy.orm import class_mapper


jwt = JWTManager(app)



# Login 
@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email")
    password = request.json.get("password")

    user = Users.query.filter_by(email=email).first()

    if user and user.authenticate_password(password):
        extra_information_claims = {"role": user.type}    #Based our model's User polymorphic_on =type
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1),    #Token expires after 1 hour
            fresh=True,                          # Ideal for logins but not routes
            additional_claims=extra_information_claims             #Thw user is signed in as who: Admin or Staff
            )

        return jsonify(access_token=access_token)
    else:
        return jsonify({"message":"Bad credentials"}, 401)



def get_current_user():
    #extracting user id from JWT token
    user_id = get_jwt_identity()

    current_user = Users.query.get(user_id)

    print(f"{current_user.first_name}")
    return current_user                         #We returning the whole object

#Permission helper: It is the 'permissions_dict' property we created in models
def check_permissions(current_user, key, value):
    """
    Check if the current user has the required permission for a specific key.
    For example: key = 'vendor', value='c' (Create)
    """

    permissions = current_user.permissions_dict     #This is user's persmissions as a dict

    if key in permissions and value in permissions[key]:
        return True
    return False


# Start of Admin dashboard

# Admin dashboard
@app.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type == "Admin":
        return jsonify({"message": "Welcome to the Admin dashboard"}), 200
    
    else:
        return jsonify({"error": "Only Admin allowed"}), 403


def has_associations(member):
    """
    Check if the staff member has any associated records in related tables.
    Returns a dictionary of relationships and whether they have records.
    """
    related_data = {}

    for relationship in class_mapper(member.__class__).relationships:
        related_records = getattr(member, relationship.key)

        if related_records and (isinstance(related_records, list) and len(related_records) > 0):
            related_data[relationship.key] = True

    return related_data


# End of Admin dashboard


# -------------------------------------------------------------
#-------------------------Staff Permissions---------------------------

# Start of Staff Permissions

# Admin - Staff
@app.route("/admin/dashboard/staff", methods=["GET", "POST"])
@jwt_required()
def admin_staff_route():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type != "Admin":
        return jsonify({"error": "Only Admin allowed"}), 403
    

    if request.method == "GET":
        all_staff = Staff.query.all()
        
        # Convert the staff objects to a serializable format
        staff_register = [staff.to_dict() for staff in all_staff]

        return jsonify(staff_register), 200  # Return with a status code 200 OK
    
    elif request.method == "POST":
        # we get data from form data
        data = request.get_json()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        username = data.get("username")
        email = data.get("email")
        date_employed = data.get("date_employed")   # This date is in a string type 
        department = data.get("department")
        employment_status = data.get("employment_status", EmploymentStatusEnum.ONGOING)
        password = data.get("password")

        #Convert date from string to python date object
        try:
            d_employed = datetime.strptime(date_employed, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
        
        #Validate the the fields
        if not first_name or not last_name or not username or not email or not department or not password:
            return jsonify({"error": "Please fill all fields"}), 400
        
        # Lets sort the department Enum: Selection from drop down menu
        try:
            department_enum = DepartmentEnum[department]
        
        except KeyError:
            return jsonify({"error": "Invalid department"}), 400
        
        #Now lets create the instance
        new_staff = Staff(
            first_name=first_name,
            last_name = last_name,
            username = username,
            email = email,
            date_employed= d_employed,
            department= department_enum,
            employment_status = employment_status,
            admin_id = current_logged_in_user.id
        )

        #set password using the password setter
        new_staff.password = password

        try:
            db.session.add(new_staff)
            db.session.commit()
            return jsonify({"message": "Staff created successfully"}), 201
        
        except Exception as e:
            db.session.rollback()   # roll back in case of an error
            return jsonify({"error": str(e)}), 500



#Admi - secific staff
@app.route("/admin/dashboard/staff/<int:id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def admin_staff_id_route(id):
    current_logged_user = get_current_user()

    if current_logged_user.type != "Admin":
        return jsonify({"Error": "Only Admin allowed"}), 403
    
    staff_member = Staff.query.get(id)
    print(f"Staff member found: {staff_member}")

    if  request.method == "GET":
        
        if not staff_member:
            return jsonify({"Error": "Staff does not exist"}), 404
        
        response = {
            "id": staff_member.id,
            "first_name": staff_member.first_name,
            "last_name": staff_member.last_name,
            "username": staff_member.username,
            "email": staff_member.email,
            "permissions": staff_member.permissions,  
            "date_employed": staff_member.date_employed.strftime("%Y-%m-%d") if staff_member.date_employed else None,
            "department": staff_member.department.name,
            "employment_status": staff_member.employment_status.name,
            "date_exited": staff_member.date_exited.stftime("%Y-%m-%d") if staff_member.date_exited else None,
        }

        return jsonify(response), 200

    elif request.method == "PATCH":
        
        if not staff_member:
            return jsonify({"Error": "Staff does not exist"}), 404
        
        data = request.get_json()

        # department Enum
        try:
            d_enum = data.get("department")
            if d_enum:      # Only process if department is provided          
                staff_department = DepartmentEnum[d_enum]
            
            else:
                staff_department = staff_member.department

        except KeyError:
            return jsonify({"Error": "Invalid department"}), 400
        
        #Date: turn it from a string to python date
        try:
            if "date_employed" in data:
                employed = data.get("date_employed")
                date_employed = datetime.strptime(employed, "%Y-%m-%d").date()
                
            else:
                date_employed = staff_member.date_employed

            if "date_exited" in data:
                exited = data.get("date_exited")
                date_exited = datetime.strptime(exited, "%Y-%m-%d").date()
            else:
                date_exited = staff_member.date_exited

        except ValueError:
            return jsonify({"Error": "Invalid date"}), 400

        try:

            staff_member.first_name = data.get("first_name", staff_member.first_name)
            staff_member.last_name = data.get("last_name", staff_member.last_name)
            staff_member.username = data.get("username", staff_member.username)
            staff_member.email = data.get("email", staff_member.email)
            staff_member.date_employed = date_employed
            staff_member.department = staff_department
            staff_member.date_exited = date_exited

            db.session.commit()
            return jsonify({"Message": "Staff member updated successfully!"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"Error": str(e)}), 400


    elif request.method == "DELETE":
        if not staff_member:
            return jsonify({"Error": "Staff member not found"}), 404

        associated_records = has_associations(staff_member)

        if associated_records:
            error_message = "Cannot delete staff member reason being has associations in: " + ", ".join(associated_records.keys())
            return jsonify({"Error": error_message}), 400

        try:
            db.session.delete(staff_member)
            db.session.commit()
            return jsonify({"Message": "Staff member deleted successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": str(e)}), 400


# End of Staff Permissions

#------------------------------------------------------------------------
#-------------------------Admin Vendor Permissions---------------------------

# Start of Vendor Permissions


# admin dashboard Vendor
@app.route("/admin/dashboard/vendor", methods=["GET", "POST"])
@jwt_required()
def admin_vendor_route():
    current_logged_user = get_current_user()

    if current_logged_user.type != "Admin":
        return jsonify({"Error": "Only Admin allowed"}), 403

    if request.method == "GET":
        all_vendors = Vendor.query.all()


        vendors = [vendor.to_dict() for vendor in all_vendors]

        return jsonify(vendors), 200

    elif request.method == "POST":
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        kra_pin = data.get("kra_pin")
        location = data.get("location")
        country = data.get("country")
        currency = data.get("currency")

        #Validate required field
        if not name or not email or not kra_pin or not phone:
            return jsonify({"Error":"Missing required fields"}), 400

        #Phone is an Integer in db
        phone_str = str(phone)

        if not phone_str.isdigit():
            return jsonify({"Error":"Phone must be a twelve digits"}), 403
        
        #Check for duplicate Vendor name and email
        existing_vendor = Vendor.query.filter((Vendor.name == name) | (Vendor.email == email)).first()

        if existing_vendor:
            return jsonify({"Error": "Vendor already exists"}), 400
        
        #Currency enum
        try:
            currency_enum = CurrencyEnum[currency]

        except KeyError:
            return jsonify({"Error":"Invalid currency key"}), 403
        
        
        #create the instance
        new_vendor = Vendor(
            name=name,
            email=email,
            phone=phone_str,
            kra_pin=kra_pin,
            location=location,
            country=country,
            currency=currency_enum,
            instance=current_logged_user
        )

        try:
            db.session.add(new_vendor)
            db.session.commit()
            return jsonify({"Message":"Vendor created successfully"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"Error": str(e)}), 400



# admin dashboard Vendor id
@app.route("/admin/dashboard/vendor/<int:id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def admin_vendor_id_route(id):

    current_logged_user = get_current_user()

    if current_logged_user.type != "Admin":
        return jsonify({"Error":"Only Admin allowed"}), 403
    
    #Getting a specific vendor
    vendor = Vendor.query.get(id)

    if request.method == "GET":
        
        try:
            if vendor:
                response ={
                    "name" : vendor.name,
                    "email" : vendor.email,
                    "phone" : vendor.phone,
                    "kra_pin" : vendor.kra_pin,
                    "location" : vendor.location,
                    "country" : vendor.country,
                    "currency" : vendor.currency.name,
                    "date_registered" : vendor.date_registered
                    }

                return jsonify(response), 200

        except Exception as e:
            return jsonify({"Error": str(e)}), 400


    elif request.method == "PATCH":

        if not vendor:
            return jsonify({"Error": "Vendor does not exist"}), 404
        
        data = request.get_json()
        
        try:
            phone_no = data.get("phone")
            if phone_no is None:
                phone = vendor.phone 

            else:        
                phone = str(phone_no)
            
        except ValueError as e:
            return jsonify({"Error": str(e)}), 400
        
        try:
            currency_enum = data.get("currency")
            if currency_enum:
                currency = CurrencyEnum[currency_enum]

            else:
                currency = vendor.currency

        except ValueError:
            return jsonify({"Error": "currency key not available"}), 400

        vendor.name = data.get("name", vendor.name)
        vendor.email = data.get("email", vendor.email)
        vendor.phone = phone
        vendor.kra_pin = data.get("kra_pin", vendor.kra_pin)
        vendor.location = data.get("location", vendor.location)
        vendor.country = data.get("country", vendor.country)
        vendor.currency = currency
        vendor.instance = current_logged_user

        try:
            db.session.add(vendor)
            db.session.commit()
            return jsonify({"Message": "Vendor updated successfully"})

        except Exception as e:
            db.session.rollback()
            return jsonify({"Error": str(e)})


    elif request.method == "DELETE":
        
        if not vendor:
            return jsonify({"Error": "Vendor not found"}), 404
        
        check_assosiation = has_associations(vendor)

        if check_assosiation:
            return jsonify({"Error":"Cannot deleted Vendor because there exist associations in: " + ", ".join(check_assosiation.keys())}), 400
        
        try:
            db.session.delete(vendor)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            return jsonify({"Error": str(e)}), 400


# End of Staff Permissions


#-------------------------Admin Customer Permissions---------------------------


# Start of Customer Permissions

#Admin gets all customer/ Admin post's a customer

@app.route("/admin/dashboard/customer", methods =["GET", "POST"])
@jwt_required()
def admin_customer_route():
    
    current_logged_user = get_current_user()

    if current_logged_user.type != "Admin":
        return jsonify({"Error":"Only admin allowed"}), 403
    
    if request.method == "GET":

        all_customers = Customer.query.all()

        customers = [customer.to_dict() for customer in all_customers]

        return jsonify(customers), 200
    
    if request.method == "POST":

        data = request.get_json()

        name = data.get("name")
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone")
        kra_pin = data.get("kra_pin")
        location = data.get("location")
        country = data.get("country")
        currency = data.get("currency")
        account_limit = data.get("account_limit")
        active = data.get("active")

        if not name or not email or not phone or not kra_pin or not location or not country or not currency or not account_limit:
            return jsonify({"Error": "All fields required!"}), 400
        
        new_customer = Customer(
            name= name,
            active=active,
            username=username,
            email=email,
            password = password,
            phone=phone,
            kra_pin=kra_pin,
            location=location,
            country=country,
            currency=CurrencyEnum[currency],
            account_limit=account_limit,
            instance = current_logged_user
        )

        try:
            db.session.add(new_customer)
            db.session.commit()
            return jsonify({"Message": "Customer created successfully!"})

        except Exception as e:
            db.session.rollback()
            return jsonify({"Error": str(e)}), 500





#Admin gets/ update's/ Delete's a specific customer
@app.route("/admin/dashboard/customer/<int:id>", methods=["GET", "PATCH", "DELETE"])
@jwt_required()
def admin_customer_id_route(id):
    
    current_logged_user = get_current_user()

    if current_logged_user.type != "Admin":
        return jsonify({"Error": "Only Admin allowed"}), 403
    
    customer = Customer.query.get(id)


    if request.method == "GET":
        
        if not customer:
            return jsonify({"Error": "Customer doesn't exist"}), 404
        
        response = {
            "account_limit": customer.account_limit,
            "active": customer.active,
            "country": customer.country,
            "currency": customer.currency.name,
            "date_enrolled": customer.date_enrolled,
            "date_last_updated": customer.date_last_updated,
            "email": customer.email,
            "kra_pin": customer.kra_pin,
            "location": customer.location,
            "phone": customer.phone,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "username": customer.username            
        }

        return jsonify(response), 200






# End of Staff Permissions




# ------------------------------------------------------------------------

#-------------------------Staff Dashboard---------------------------

# Start of Staff Dashboard


# Staff dashboard
@app.route("/staff/dashboard", methods=["GET"])
@jwt_required()
def staff_dashboard():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type == "Staff":
        return jsonify({"message":"Welcome to the staff dashboard"}), 200
    
    else:
        return jsonify({"error": "Only Staff allowed!!!"}), 403










# End of Staff Dashboard







# Customer dashboard
@app.route("/customer/dashboard", methods=["GET"])
@jwt_required()
def customer_dashboard():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type == "Customer":
        return jsonify({"message": "Welcome to Customer Dashboard"}), 200
    
    else:
        return jsonify({"message": "Only customers allowed!!!"}), 403













if __name__ == "__main__":
    app.run(debug=True)