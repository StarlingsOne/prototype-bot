# intake_streams/stlouisfred.py

FRED_URL_TEMPLATE = (
    "https://api.stlouisfed.org/fred/series/observations?"
    "series_id=SP500"
    "&api_key={api_key}"
    "&file_type=json"
    "&observation_start={start}"
    "&observation_end={end}"
    "&frequency=d"
)

def build_fred_url(api_key, start, end):
    return FRED_URL_TEMPLATE.format(api_key=api_key, start=start, end=end)
