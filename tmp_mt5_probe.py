import sys
print("venv ok")
try:
    import MetaTrader5 as mt5
    print("mt5 module ok")
    if mt5.initialize():
        print("mt5 initialized")
        acct = mt5.account_info()
        print("account:", acct)
        mt5.shutdown()
    else:
        print("mt5 initialize failed")
except Exception as e:
    print(f"mt5 error: {e}")
