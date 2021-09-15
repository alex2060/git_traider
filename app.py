from flask import Flask, redirect, url_for, render_template, request, flash
import os
from os.path import join, dirname
from dotenv import load_dotenv
import braintree
from gateway import generate_client_token, transact, find_transaction
load_dotenv()
import requests

#makes and retruns crypto key
def make_qr_code():
    path = "http://alexhaussmann.com/adhaussmann/a_final/"
    command= "add_key_dev.php?uname=ptest_led&password=pass&email=ReceiverEmail"
    x = requests.get(path+command)

    val = str(x.content)
    out = val.split(" ")
    print(out[1]+"-"+out[2])
    return out[1]+"-"+out[2]


def convert(mystuff):
    out = mystuff.split("-")
    return "http://alexhaussmann.com/adhaussmann/a_final/output2.php?key="+out[1]+"&name="+out[0]+"&entery_name=ptest_led"
#myval = make_qr_code()


app = Flask(__name__)
app.secret_key = os.environ.get('APP_SECRET_KEY')

PORT = int(os.environ.get('PORT', 4567))

TRANSACTION_SUCCESS_STATUSES = [
    braintree.Transaction.Status.Authorized,
    braintree.Transaction.Status.Authorizing,
    braintree.Transaction.Status.Settled,
    braintree.Transaction.Status.SettlementConfirmed,
    braintree.Transaction.Status.SettlementPending,
    braintree.Transaction.Status.Settling,
    braintree.Transaction.Status.SubmittedForSettlement
]

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('new_checkout'))

@app.route('/checkouts/new', methods=['GET'])
def new_checkout():
    client_token = generate_client_token()
    return render_template('checkouts/new.html', client_token=client_token)

@app.route('/checkouts/<transaction_id>', methods=['GET'])
def show_checkout(transaction_id):
    out = transaction_id.split("_")

    transaction = find_transaction(out[0])
    result = {}
    if transaction.status in TRANSACTION_SUCCESS_STATUSES:
        result = {
            'header': 'Sweet Success!',
            'icon': 'success',
            'message': 'Your test transaction has been successfully processed. See the Braintree API response and try again.',
            'link' : convert(out[1])
        }
    else:
        result = {
            'header': 'Transaction Failed',
            'icon': 'fail',
            'message': 'Your test transaction has a status of ' + transaction.status + '. See the Braintree API response and try again.',
            'link' : ""
        }

    return render_template('checkouts/show.html', transaction=transaction, result=result)

@app.route('/checkouts', methods=['POST'])
def create_checkout():


    result = transact({
        'amount': request.form['amount'],
        'payment_method_nonce': request.form['payment_method_nonce'],
        'options': {
            "submit_for_settlement": True
        }
    })

    if result.is_success:
        val = make_qr_code()

    if result.is_success or result.transaction:
        print("in here")


        print(request.form['amount'])
        return redirect(url_for('show_checkout',transaction_id=result.transaction.id+"_"+val ))
    else:
        for x in result.errors.deep_errors: flash('Error: %s: %s' % (x.code, x.message))
        return redirect(url_for('new_checkout'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
