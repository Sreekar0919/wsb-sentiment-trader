import json

# Load the JSON data
with open("weekly_ticker_counts.json", "r") as file:
    data = json.load(file)

# Updated list of common words to remove
common_words = {
    "EU", "UK", "WTF", "APP", "GOOD", "NICE", "FA", "WAY", "SELF", "VS", "RR", "REAL", "MOVE", "GAME", "GO", "FOX", "TECH", "HIND", "HOPE", "IRON", "ELSE", "ANY", "CASH", "HERE", "LINE"
}

# Remove common words from the data
for week, tickers in data.items():
    for word in common_words:
        tickers.pop(word, None)

# Save the cleaned data back to the JSON file
with open("weekly_ticker_counts.json", "w") as file:
    json.dump(data, file, indent=4)

print("Common words removed successfully.")
