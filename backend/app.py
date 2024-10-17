from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
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
        claims = {"role": user.type}    #Based our model's User polymorphic_on =type
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1),    #Token expires after 1 hour
            fresh=True,                          # Ideal for logins but not routes
            additional_claims=claims             #Thw user is signed in as who: Admin or Staff
            )

        return jsonify(access_token=access_token)
    else:
        return jsonify({"message":"Bad credentials"}, 401)



def get_current_user():
    #extracting user id from JWT token
    user_email = get_jwt_identity()

    current_user = Users.query.get(user_email)

    print(f"{current_user.first_name}")
    return current_user

#Permission helper
def check_permissions(current_user, resource, action):
    """
    Check if the current user has the required permission for a specific resource.
    For example: resource = 'vendor', action='c' (Create)
    """

    permissions = current_user.permissions_dict     #This is user's persmissions as a dict

    if resource in permissions and action in permissions[resource]:
        return True
    return False


if __name__ == "__main__":
    app.run(debug=True)