CONTEXT_SCHEMA = {
    "question_title": {
        "type": str,
        "desc": "The prediction market question being evaluated."
    },
    "resolution_datetime": {
        "type": str,
        "desc": "Market's resolution time (ISO8601 string, UTC)."
    },
    "hours_to_resolution": {
        "type": float,
        "desc": "Hours from now until market resolves."
    },
    "market_current_probability": {
        "type": float,
        "desc": "The most recent probability (current market price)."
    },
    "market_total_volume": {
        "type": float,
        "desc": "Total amount traded in the market."
    },
    "bot_balance": {
        "type": int,
        "desc": "Bot/user account balance."
    },
    "maximum_debt_allowed": {
        "type": int,
        "desc": "The lowest negative balance allowed for any user (e.g., -500 means the user can go down to -500)."
    },
    "topic": {
        "type": str,
        "desc": "Topic or asset identifier."
    },
    "headlines": {
        "type": str,
        "desc": "Recent news headlines, formatted for prompt input."
    },
    "sp500_fred_api_price_7_day_history": {
        "type": list,
        "desc": "Historical S&P 500 closing prices from FRED. List of dicts: [{date, value}]."
    },
    "today_datetime_utc": {
        "type": str,
        "desc": "Current UTC datetime in ISO8601 format."
    },
}