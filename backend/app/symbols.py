NSE_SYMBOL_UNIVERSE = [
    {"symbol": "RELIANCE", "name": "Reliance Industries"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank"},
    {"symbol": "SBIN", "name": "State Bank of India"},
    {"symbol": "TATASTEEL", "name": "Tata Steel"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel"},
    {"symbol": "INFY", "name": "Infosys"},
    {"symbol": "TCS", "name": "Tata Consultancy Services"},
    {"symbol": "ITC", "name": "ITC Limited"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever"},
    {"symbol": "LT", "name": "Larsen & Toubro"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank"},
    {"symbol": "AXISBANK", "name": "Axis Bank"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical"},
    {"symbol": "TITAN", "name": "Titan Company"},
    {"symbol": "WIPRO", "name": "Wipro"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints"},
]

# Nifty 50 index. "^" prefix tells _yf_symbol() in data_source.py to leave it
# as-is instead of appending ".NS" (that suffix is only for individual equities).
INDEX_SYMBOL = "^NSEI"