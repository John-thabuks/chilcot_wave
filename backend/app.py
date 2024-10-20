from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity, jwt_required
from flask import request, jsonify
from datetime import timedelta

api = Api(app)

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