from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, create_access_token
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
        access_token = create_access_token(
            identity={"email":email},
            expires_delta=timedelta(hours=1),    #Token expires after 1 hour
            fresh=True
            )
        
        return jsonify(access_token=access_token)
    else:
        return jsonify({"message":"Bad credentials"}, 401)





if __name__ == "__main__":
    app.run(debug=True)