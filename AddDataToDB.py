import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://attendance-system-207cf-default-rtdb.firebaseio.com/'
})

ref = db.reference('Student')

data = {
    'CI0001': {
        "Name": "DEEPAK V.",
        "Total_Attendance": 0,
        "Last_attendance_time": "00:00",
        "Date" : "2023-06-15"
    },
    'CI0002': {
        "Name": "ANUSHKA",
        "Total_Attendance": 0,
        "Last_attendance_time": "00:00",
        "Date" : "2023-06-15"
    },
    
    }


for key, value in data.items():
    ref.child(key).set(value)
