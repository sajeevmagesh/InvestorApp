import time
from pymongo import MongoClient
import stripe
from datetime import datetime

# Initializing connection to MongoDB
client = MongoClient(
    'mongodb+srv://Boomer:Boomer123@cluster0.u0tdb.mongodb.net/restdb?retryWrites=true&w=majority')
db = client["restdb"]

stripe.api_key = "sk_test_51IQzm5Cf6QQhScZzDFSfRq03X3a2m2lhQY1EiE50HoshfesexD3e2wjIZRdRzuFWxw9sSp1ENMv2OKNf2NkTLaGm00rcl82C6S"


def algo():
    dt = datetime.today()
    money = db.pot.find_one({"year": str(dt.year)})["money"]
    
    output = []
    total_money = []
    adding = []
    finalout = []
    for s in db.loans.find():
        output.append(s)

    for item in output:
        if str(dt.year) == item["date"][:4]:
            total_money.append([item["email"], int(item["amount"])])
            adding.append(0)
    tempList=[]
    final=[]
    for x in total_money:
        tempList.append(x[1])
    tempList.sort()
    for y in tempList:
        for x in total_money:
            if x[1]==y:
                final.append(x)
                total_money.remove(x)
    print(final)
    total_money=[]
    total_money=final
    loanees = len(total_money)
    avg = int(money)/loanees

    for x in range(loanees):
        if avg + adding[x] > total_money[x][1]:
            if x != loanees-1:
                adding[x+1] = avg + adding[x] - total_money[x][1]
        if total_money[x][1] < avg + adding[x]:    
            finalout.append([total_money[x][1], total_money[x][0]])
        elif total_money[x][1] >= avg + adding[x]:
            finalout.append([avg+adding[x], total_money[x][0]])  
    print(finalout)
    for x in range(len(finalout)):
        stripe.Transfer.create(
            amount=int(finalout[x][0]),
            currency="usd",
            destination=str(db.stripe.find_one({"email": str(finalout[x][1])})["stripe"]),
        )

    return final

algo()
