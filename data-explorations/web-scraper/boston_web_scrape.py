"""
This is a first attempt at web-scraping Boston's DBA database from their website.
1) request and pull the data by neighborhood
2) download and parse the html into a proper excel doc
3) use pandas for a bit of data cleaning and concatenate the results
4) write to file
"""

import requests
import time
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

neighborhoods = [
    "Allston", "Back Bay", "Bay Village", "Beacon Hill", "Brighton",
    "Charlestown", "Chinatown", "Dorchester (North)", "Dorchester (South)",
    "Downtown", "East Boston", "Fenway/Kenmore", "Hyde Park", "Jamaica Plain",
    "Mattapan", "Mission Hill", "North End", "Roslindale", "Roxbury",
    "South Boston", "South End", "West End", "West Roxbury"
]

session = requests.Session()
all_data = []

for neighborhood in neighborhoods:
    url = f"https://www.cityofboston.gov/cityclerk/dbasearch/Default.aspx?business_neighborhood={neighborhood}"
    
    # GET the page
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    r = session.get(url)
    print(f"Searching: {neighborhood}")  # confirm the URL is correct
    print("results found" if "File Number" in r.text else "NO RESULTS in GET response")
    
    # Extract hidden ASP.NET fields
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

    payload = {
        "__VIEWSTATE": viewstate["value"] if viewstate else "",
        "__VIEWSTATEGENERATOR": viewstate_gen["value"] if viewstate_gen else "",
        "__EVENTVALIDATION": event_validation["value"] if event_validation else "",
        "RadGrid1$ctl00$ctl02$ctl00$ExportToExcelButton": " ",
        "business_neighborhood": neighborhood,
    }
    
    ###POST to trigger the export
    export = session.post(url, data=payload)
    
    # Parse as HTML table instead of Excel
    
    tables = pd.read_html(BytesIO(export.content))
    
    if tables:
        df = tables[0]  # take the first table
        df["Neighborhood"] = neighborhood
        all_data.append(df)
        print(f"✓ {neighborhood} — {len(df)} rows")
    else:
        print(f"✗ {neighborhood} — no table found")
    time.sleep(1)

###Combine and save
combined = pd.concat(all_data, ignore_index=True)
combined.to_excel("boston_dba_full.xlsx", index=False)
print(f"\nDone — {len(combined)} total rows saved to boston_dba_full.xlsx")