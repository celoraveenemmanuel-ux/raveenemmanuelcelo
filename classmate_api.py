
import requests

url = "https://balcenajessicaann.onrender.com/profile"

response = requests.get(url)
if response.status_code == 200:
    data = response.json()

    print("\n--- Classmate Student Information ---")
    print("Name:", data["name"])
    print("Email:", data["email"])
    print("Student ID:", data["student_id"])
    print("Program:", data["program"])
    print("Year:", data["year"])
    print("Section:", data["section"])
    print("Skills:", ", ".join(data["skills"]))

else:
    print("Request failed.")
    print("Status Code:", response.status_code)
