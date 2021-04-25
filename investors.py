# Web handler (Flask) import
from re import DOTALL
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, g, Blueprint
import stripe
# Database (MongoDB) imports
from pymongo import MongoClient, database
from bson.objectid import ObjectId
from base64 import b64encode
import gridfs
import io
import os
import requests
from datetime import datetime
# Initializing connection to MongoDB
client = MongoClient(
    'mongodb+srv://Boomer:Boomer123@cluster0.u0tdb.mongodb.net/restdb?retryWrites=true&w=majority')
db = client["restdb"]

investors = Blueprint('investors', __name__)
stripe_keys = {
    'secret_key': 'sk_test_51IQzm5Cf6QQhScZzDFSfRq03X3a2m2lhQY1EiE50HoshfesexD3e2wjIZRdRzuFWxw9sSp1ENMv2OKNf2NkTLaGm00rcl82C6S',
    'publishable_key': 'pk_test_51IQzm5Cf6QQhScZzRfowUm5lMRG2r57bcC1bD7moPdFv7DlfJCNMaFGC1Nsi91ILwUMlWUoGrZrzjwc13irM8cVe00yjAJR8M6'
}
text = ""
amount = ""
id = ""
stripe.api_key = stripe_keys['secret_key']


@investors.route('/investors', methods=['GET', 'POST'])
def pay():
    global text, amount
    if 'user' in session:
        print(session['user'])
        if request.method == 'GET':
            return render_template("investors.html", name=session['user'])
        else:
            return redirect("/count")
    return render_template("login.html", message="Please log in before continuing.", style="warning")


@investors.route('/count', methods=['GET', 'POST'])
def prepay():
    global text, amount
    if 'user' in session:
        if request.method == 'GET':
            return render_template("count.html")
        else:
            text = request.form['text']
            amount = " $"+str(text)+".00"
            print(amount, text)
            text = int(text)*100
            print(text)
            return redirect("/create-checkout-session")
    return render_template("login.html", message="Please log in before continuing.", style="warning")

@investors.route('/create-checkout-session', methods=['GET', 'POST'])
def confirmPayment():
    global text, amount, id
    print(amount)

    if 'user' in session:
        if request.method == 'GET':
            print(amount)
            return render_template("buy.html", amount=amount)
        else:

            sessions = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': 'Loan',
                        },
                        'unit_amount': text,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url='https://hopevest.herokuapp.com/checkoutsuccess',
                cancel_url='https://hopevest.herokuapp.com/investors',

            )
            id = sessions.id
            return jsonify(id=sessions.id)
    return render_template("login.html", message="Please log in before continuing.", style="warning")


@investors.route('/checkoutsuccess', methods=['GET'])
def checkout():
    global text, amount, id
    if 'user' in session:
        sessions = stripe.checkout.Session.retrieve(
            id,
        )
        if sessions.payment_status == "paid":
            dt = datetime.today()
            if dt.month >= 8:
                # If money given not during school times, but it in a database to later be distributed
                if db.pot.count_documents({"year": str(dt.year+1)}) >= 1:
                    current_money = db.pot.find_one(
                        {"year": str(dt.year+1)})["money"]
                    db.pot.update_one({"year": str(dt.year+1)}, {
                                      "$set": {"money": int(current_money) + int(text)}})
                else:
                    rec = {"year": str(dt.year+1), "money": int(text)}
                    db.pot.insert_one(rec)
                            # If money given not during school times, but it in a database to later be distributed
            else:
                if db.pot.count_documents({"year": str(dt.year)}) >= 1:
                    current_money = db.pot.find_one(
                        {"year": str(dt.year)})["money"]
                    print(str(dt.year))
                    money=int(current_money) + int(text)
                    db.pot.update_one({"year": str(dt.year)}, {
                                        "$set": {"money": money}})
                else:
                    rec = {"year": str(dt.year), "money": int(text)}
                    db.pot.insert_one(rec)

                


        return render_template('checkout.html', amount=amount)
    return render_template("login.html", message="Please log in before continuing.", style="warning")