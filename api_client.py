import requests

url = "https://raveenemmanuelcelo.onrender.com/motorcycle"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    print("Motorcycle Name:", data["motorcycle_name"])
    print("Brand:", data["brand"])
    print("Engine CC:", data["engine_cc"])
    print("Price:", data["price"])
    print("Available:", data["available"])

else:
    print("Request failed.")
    print("Status Code:", response.status_code)
