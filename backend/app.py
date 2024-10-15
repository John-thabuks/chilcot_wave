from config import app, db
from models import Users, Admin, Staff,CurrencyEnum, Customer, Vendor, Invoice, Purchase, VatEnum, Item, Category, SerialNumber, Currency, Lpo, PaymentModeEnum, Payment, Quotation, DeliveryNote, JobCardStatus, JobCard
from flask_restful import Resource, Api

api = Api(app)

# Admin features
class Admin(Resource):
    pass



# Staff features
class Staff(Resource):
    pass    


#Invoice
class Invoice(Resource):
    pass

class Purchases(Resource):
    pass

class DeliveryNote(Resource):
    pass

api.add_resource(Admin, "/admin")
api.add_resource(Staff, "/staff")
api.add_resource(Invoice, "/invoice")
api.add_resource(Purchase, "/purchase")
api.add_resource(DeliveryNote, "/delivery_note")




@app.route("/")
def index():
    return "Hello there"

if __name__ == "__main__":
    app.run(debug=True)