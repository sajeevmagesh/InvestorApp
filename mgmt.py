# Web handler (Flask) import
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from itsdangerous import URLSafeTimedSerializer
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, g, Blueprint
import stripe
# Database (MongoDB) imports
from pymongo import MongoClient
from bson.objectid import ObjectId
from base64 import b64encode
import gridfs
import io

# Initializing connection to MongoDB
client = MongoClient(
    'mongodb+srv://Boomer:Boomer123@cluster0.u0tdb.mongodb.net/restdb?retryWrites=true&w=majority')
db = client["restdb"]

# Initializing connection to MongoDB image collections
# https://docs.mongodb.com/manual/core/gridfs/
gs = gridfs.GridFS(db, collection="gs")

# Link expiration
s = URLSafeTimedSerializer('basingse')

# Email sending packages

# Environment variables
load_dotenv()
stripe.api_key = "sk_test_51IQzm5Cf6QQhScZzDFSfRq03X3a2m2lhQY1EiE50HoshfesexD3e2wjIZRdRzuFWxw9sSp1ENMv2OKNf2NkTLaGm00rcl82C6S"
# Getting environment variables
email_name = os.getenv("NAME")
email_domain = os.getenv("DOMAIN")
email_password = os.getenv("PASSWORD")
email_name="crowdsourcedstudentloans"
email_domain="gmail.com"
email_password="SajeevRohan"
# Printing environment variables
print("Email name:", email_name)
print("Email domain:", email_domain)
print("Email password:", email_password)

mgmt = Blueprint('mgmt', __name__)
@mgmt.route('/', methods=['GET'])
def redir():
    return redirect(url_for("mgmt.login"))
@mgmt.route('/login', methods=['GET', 'POST'])
def login():
    """ Login to the application with previously created credentials stored in the database. """
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['pass']
        document = {"email": email, "password": password}
        user_document = {"email": email}
        verified_document = {"email": email,
                             "password": password, "verified": True}

        if db.users.find(user_document).count() > 0:
            if db.users.find(document).count() > 0:
                if db.users.find(verified_document).count() > 0:
                    session['user'] = email
                    g.user=session['user']
                    if db.users.count_documents({"email": session['user'], "account_type": "student", "profile": False}) != 0:
                        return redirect(url_for("mgmt.verify_profile"))
                    else:
                        if db.users.count_documents({"email": session['user'], "account_type": "student", "profile": True}) != 0:
                            return redirect(url_for("user.landing"))
                        else:        
                            return redirect(url_for("investors.pay"))
                else:
                    send_email(email)
                    return render_template("login.html", message="Make sure your account has been verified! We resent your verification email.", style="warning")
            else:
                return render_template("login.html", message="Incorrect password.", style="danger")
        else:
            return render_template("login.html", message="An account with that email address does not exist.", style="danger")
    return render_template("login.html")

@mgmt.route("/signup", methods=["GET", "POST"])
def signup():
    """ Create credentials stored in the database to later login to the application. """
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['pass']
        account_type = request.form['type']

        query = {"email": email}
        account = stripe.Account.create(
            type='express',
            email=email
        )

        rec = {"email": email, "stripe": account.id, "type": account_type}
        db.stripe.insert_one(rec)

        # Checking if the entered email exists
        if db.users.find(query).count() > 0:
            return render_template("signup.html", message="That email address already has an account.", style="danger")
        else:
            document = {"name": name, "email": email, "password": password,
                        "verified": False, "account_type": account_type, "profile": False}
            send_email(email)
            db.users.insert_one(document)
            link = stripe.AccountLink.create(
                account=account.id,
                refresh_url="https://example.com/reauth",
                return_url="https://dreamvester.herokuapp.com/login",
                type="account_onboarding",
            )
            print(link.url)
            return redirect(link.url)
            # not needed anymore :-- return render_template("signup.html", message=f"Your account has been created! Check your email to verify your account and get started! The link expires in an hour!", style="success")
    return render_template("signup.html")

@mgmt.route('/verify/<token>', methods=["GET"])
def verify(token):
    """ Verify the account of a user when they access a link. """
    email = request.args.get('email')
    url = s.loads(token, salt='email-confirm', max_age=3600)
    myquery = {"email": email}
    newvalues = {"$set": {"verified": True}}

    db.users.update_one(myquery, newvalues)

    return render_template("login.html", message="Email confirmed. You can log in now!", style="success")


def send_email(email):
    """ Generate a verification link and send an email to verify a user's account. """
    token = s.dumps(email, salt='email-confirm')
    URL = f"https://dreamvester.herokuapp.com/verify/{token}?email={email}"

    # me == my email address
    # you == recipient's email address
    me = f"{email_name}@{email_domain}"
    target = email

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Verification"
    msg['From'] = me
    msg['To'] = target

    # Create the body of the message (a plain-text and an HTML version).
    text = f"Hi!\nClick on the following link to verify your account:\n{URL}"
    html = f"""\
    <html>
      <head></head>
      <body>
        <p>Hi!<br>
           Click on <a href="{URL}">this</a> link to verify your account.
        </p>
      </body>
    </html>
    """

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)
    # Send the message via local SMTP server.
    mail = smtplib.SMTP('smtp.gmail.com', 587)

    mail.ehlo()

    mail.starttls()

    mail.login(email_name, email_password)
    mail.sendmail(me, target, msg.as_string())
    mail.quit()


@mgmt.route('/user', methods=['GET'])
def current_user():
    """ Print the current user. Currently used for testing purposes. """

    return render_template("login.html", message="Please log in before continuing.", style="warning")


@mgmt.route("/signout", methods=['GET'])
def signout():
    """ Lets the user sign out of the application. """
    if "user" in session:
        session.clear()
        return render_template("login.html", message="Successfully logged out!", style="success")
    return render_template("login.html", message="Make sure you are logged in!", style="warning")


@mgmt.route("/verify_profile", methods=['GET', 'POST'])
def verify_profile():
    if "user" in session:
        if request.method == 'GET':
            return render_template("student_verify.html")
        else:
            name = request.form['full_name']
            school = request.form['institution']
            proof = request.files['proof']
            proof = gs.put(proof, encoding='utf-8')
            backgroundcheck = request.files['backgroundcheck']
            backgroundcheck = gs.put(backgroundcheck, encoding='utf-8')

            rec = {"name": name,
                   "school": school,
                   "email": session['user'],
                   "proof": proof,
                   "backgroundcheck": backgroundcheck}

            db.verifications.insert_one(rec)

            db.users.update_one({"email": session['user']}, {"$set": {"profile": True}})


            return redirect(url_for("user.landing"))

    return render_template("login.html", message="Make sure you are logged in!", style="warning")
