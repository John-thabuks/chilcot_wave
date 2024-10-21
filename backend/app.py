from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard, DepartmentEnum, EmploymentStatusEnum
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask import request, jsonify
from datetime import datetime, timedelta


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



# Admin dashboard
@app.route("/admin/dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type == "Admin":
        return jsonify({"message": "Welcome to the Admin dashboard"}), 200
    
    else:
        return jsonify({"error": "Only Admin allowed"}), 403


# Admin - Staff
@app.route("/admin/staff", methods=["GET", "POST"])
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

        #Convert date from string to python date object
        try:
            d_employed = datetime.strptime(date_employed, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400
        
        #Validate the the fields
        if not first_name or not last_name or not username or not email or not department:
            return jsonify({"error": "Please fill all fields"}), 400
        
        # Lets sort the department Enum
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
            employment_status = employment_status
        )

        db.session.add(new_staff)
        db.session.commit()

        return jsonify(new_staff.to_dict()), 201



#Admi - secific staff
app.route("/admin/staff/<int:id>", methods=["GET", "POST", "PATCH", "DELETE"])
@jwt_required()
def admin_staff_id_route(id):
    current_logged_user = get_current_user()

    if current_logged_user.type == "Admin":
        if request.method == "GET":
            pass

        elif request.method == "POST":
            pass

        elif request.method == "PATCH":
            pass

        else:
            pass
            



# Staff dashboard
@app.route("/staff/dashboard", methods=["GET"])
@jwt_required()
def staff_dashboard():
    current_logged_in_user = get_current_user()

    if current_logged_in_user.type == "Staff":
        return jsonify({"message":"Welcome to the staff dashboard"}), 200
    
    else:
        return jsonify({"error": "Only Staff allowed!!!"}), 403






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