import requests
url = "https://raveenemmanuelcelo.onrender.com/student"
response = requests.get(url)
print(response.text)