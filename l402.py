import requests
import pymacaroons
lnaddress = "bitcointraveler@blink.sv"

def parse_lnaddress(lnaddress):
    [ name, domain ] = lnaddress.split("@")
    return [name, domain]

def get_callback(name, domain):
    res = requests.get("https://"+domain+"/.well-known/lnurlp/"+name)
    print(res.json())
    return res.json()["callback"]

name, domain = parse_lnaddress(lnaddress)
callback = get_callback(name, domain)

def get_invoice(callback, amount):
    res = requests.get(callback + "?amount=" + str(amount))
    print(res.json())
    return res.json()["pr"]

def getL402(msats):
    invoice = get_invoice(callback, msats)
    l402 = "L402 token=placeholder, invoice="+invoice
    return l402
