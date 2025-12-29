import json
import requests

# Du kannst PATCH später ändern (oder ich zeig dir gleich "latest")
PATCH = "14.1.1"
LANG = "en_US"

url = f"https://ddragon.leagueoflegends.com/cdn/{PATCH}/data/{LANG}/championFull.json"
data = requests.get(url, timeout=20).json()

out = []
for champ in data["data"].values():
    name = champ["name"]  # Anzeigename (z.B. "Kai'Sa")
    file_key = champ["image"]["full"].replace(".png", "")  # Dateiname ohne .png (z.B. "Kaisa")
    img = f"https://ddragon.leagueoflegends.com/cdn/{PATCH}/img/champion/{file_key}.png"
    out.append({"name": name, "image": img})

out.sort(key=lambda x: x["name"].lower())

with open("champions.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Wrote champions.json:", len(out))
