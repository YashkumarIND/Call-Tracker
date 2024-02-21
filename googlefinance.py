import serpapi as serpapi
from serpapi import GoogleSearch

params = {
  "engine": "google_finance",
  "q": "RELIANCE:NSE",
  "api_key": "4bdc90ff4790171cf473075bcd717c27b3c25777d35ddefd07a3fd6187e8f6da"
}

search = GoogleSearch(params)
results = search.get_dict()
print(results["summary"]["price"])