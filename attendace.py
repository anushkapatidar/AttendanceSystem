import tkinter as tk
import cv2
import pickle
import time
import numpy as np
import face_recognition
from PIL import Image, ImageTk
import os
from openpyxl import load_workbook
from tkinter import messagebox
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://attendance-system-207cf-default-rtdb.firebaseio.com/',
    'storageBucket': 'attendance-system-207cf.appspot.com'
})

# Create the main window
window = tk.Tk()
window.title("Button Window")
window.configure(bg="#e6f5ff")
processed_matches=set()
df=None
############ Create new user #############
def open_new_window():
    window1 = tk.Toplevel(window)
    window1.title("New Window")
    window1.configure(bg="#e6f5ff")

    label = tk.Label(window1, text="REGISTER YOURSELF", font=("Arial", 22, 'bold'), fg='#4db8ff', bg="#e6f5ff")
    label.grid(row=0, column=0, columnspan=2, pady=20, padx=20)

    def new_users():
        # Function to handle new user registration
        ci_id = entry_id.get()
        name = entry_name.get()
        des = entry_des.get()
        now = datetime.now()
        cdate = now.strftime("%Y:%m:%d")
        ctime = now.strftime("%H:%M:%S")
        label1 = tk.Label(window1)
        label1.grid(row=1, column=0, columnspan=2, padx=10, pady=10)
        # add data to firebase database
        def insert_data_to_firebase():
            # Get a reference to the 'Student' node
            ref = db.reference('Student')

            data = {
                ci_id: {
                    "Name": name,
                    "Total_Attendance": 0,
                    'Designation': des,
                    "Last_attendance_time": ctime,
                    "Date": cdate
                }
            }

            # Insert the data into Firebase
            for key, value in data.items():
                ref.child(key).set(value)

        # encode the data
        def encode():
            

            folderPath = 'captured_photos'
            pathList = os.listdir(folderPath)
            imgList = []
            studentIds = []

            for path in pathList:
                image = cv2.imread(os.path.join(folderPath, path))
                if image is None:
                    # print(f"Failed to load image: {path}")
                    continue

                # Convert the image to a supported depth
                image = cv2.convertScaleAbs(image)

                imgList.append(image)
                name = os.path.splitext(path)[0]
                names = name.split('_')[0]
                studentIds.append(names)

                fileName = f'{folderPath}/{path}'
                bucket = storage.bucket()
                blob = bucket.blob(fileName)
                blob.upload_from_filename(fileName)

            def findEncodings(imagesList):
                encodeList = []
                for img in imagesList:
                    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_img)
                    if len(face_locations) == 0:
                        # print("No face found in image.")
                        continue

                    face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
                    encodeList.extend(face_encodings)

                return encodeList

            # Load existing encoded data if available
            if os.path.exists("shape_predictor_68_face_landmarks.dat"):
                file = open("shape_predictor_68_face_landmarks.dat", 'rb')
                encodeListKnownWithIds = pickle.load(file)
                file.close()
                existingEncodeListKnown, existingStudentIds = encodeListKnownWithIds
                imgList += existingEncodeListKnown
                studentIds += existingStudentIds

            encodeListKnown = findEncodings(imgList)
            encodeListKnownWithIds = [encodeListKnown, studentIds]

            file = open("shape_predictor_68_face_landmarks.dat", 'wb')
            pickle.dump(encodeListKnownWithIds, file)
            file.close()
            # print("Done")
            messagebox.showinfo("Registration", "User '{}' registered successfully!".format(ci_id))

        save_folder = os.path.join('captured_photos')
        cap = cv2.VideoCapture(0)

        
        time.sleep(5)
        for x in range(1):
            ret, frame = cap.read()
            frame = frame[120:120 + 380, 200:200 + 380, :]
            
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            label1.config(image=imgtk)
            label1.image = imgtk
            new_filename = os.path.join(save_folder, ci_id + "_{}.jpg".format(x + 1))
            cv2.imwrite(new_filename, frame)
            cv2.imshow('image', frame)
            
            x += 1
            
        cap.release()
        cv2.destroyAllWindows()
        insert_data_to_firebase()
        encode()
        


    # name
    entry_name_label = tk.Label(window1, text="Enter Your Name:", font=("Arial", 14), fg='#4db8ff', bg="#e6f5ff")
    entry_name_label.grid(row=2, column=0, padx=20, pady=10)
    entry_name = tk.Entry(window1, width=30, font=("Arial", 14))
    entry_name.grid(row=2, column=1, padx=20, pady=10)

    # id
    entry_id_label = tk.Label(window1, text="Enter Your 5 digit ID:", font=("Arial", 14), fg='#4db8ff', bg="#e6f5ff")
    entry_id_label.grid(row=3, column=0, padx=20, pady=10)
    entry_id = tk.Entry(window1, width=30, font=("Arial", 14))
    entry_id.grid(row=3, column=1, padx=20, pady=10)

    # Designation
    entry_des_label = tk.Label(window1, text="Enter Your Designation:", font=("Arial", 14), fg='#4db8ff',
                               bg="#e6f5ff")
    entry_des_label.grid(row=4, column=0, padx=20, pady=10)
    entry_des = tk.Entry(window1, width=30, font=("Arial", 14))
    entry_des.grid(row=4, column=1,padx=20, pady=10)

    button_register = tk.Button(window1, text="Register", width=20, height=1, command=new_users, font=("Arial", 14), bg="#99d6ff")
    button_register.grid(row=5, column=0, columnspan=1,  pady=20, padx=30)

    #exit button
    button_exit = tk.Button(window1, text="Exit", width=20, height=1, command=lambda: window1.destroy(), font=("Arial", 14), bg="#99d6ff")
    button_exit.grid(row=5, column=1, pady=20, padx=20)

############ Take attendance #############
def startt():
    file = open('shape_predictor_68_face_landmarks.dat', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds

    capp = cv2.VideoCapture(0)

    # Create a label to display the video screen
    processed_faces = set()

    def capture_frames():
        global df
        ret, frame = capp.read()
        cv2.imshow("Attendance", frame)
        faceCurFrame = face_recognition.face_locations(frame)
        encodeCurFrame = face_recognition.face_encodings(frame, faceCurFrame)

        if faceCurFrame:
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                faceId = None
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)

                if matches[matchIndex] and faceDis[matchIndex] < 0.5:
                    faceId = studentIds[matchIndex]

                if faceId is not None and faceId not in processed_faces:
                    processed_faces.add(faceId)
                    student_info = db.reference(f'Student/{faceId}').get()
                    datetimeObject = datetime.strptime(student_info['Last_attendance_time'], "%H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()

                    if secondsElapsed > 130:  # 130 seconds
                        ref = db.reference(f'Student/{faceId}')
                        student_info['Total_Attendance'] += 1
                        ref.child('Total_Attendance').set(student_info['Total_Attendance'])
                        ref.child('Last_attendance_time').set(datetime.now().strftime("%H:%M:%S"))
                        ref.child('Date').set(datetime.now().strftime("%Y-%m-%d"))

                        present = 'Yes'
                        # messagebox.showinfo("Attendance","'{}' You are marked present!\nAnd your total attendance is {}".format(student_info['Name'], student_info['Total_Attendance']))
                        df = pd.concat(
                            [df, pd.DataFrame({'Name': [student_info['Name']], 'ID': [faceId], 'Present': [present],
                                               'Time of Attendance': [student_info['Last_attendance_time']],
                                               'Date': [student_info['Date']]})], ignore_index=True)
                        
                        
                    message = "'{}' : Marked Present!".format(student_info['Name'])

                    create_headless_messagebox(window, message)

        window.after(10, capture_frames)

    capture_frames()

def create_headless_messagebox(parent, message):
    top_level = tk.Toplevel(parent)
    top_level.overrideredirect(True)  # Remove title bar and borders
    top_level.geometry("+150+250")  # Set the position of the messagebox

    label = tk.Label(top_level, text=message, bg='black', fg='white', font=('Helvetica', 18, 'bold'), padx=10, pady=10)
    label.pack()

    def close_messagebox():
        top_level.destroy()

    top_level.after(4000, close_messagebox)  # Close the messagebox after 3 seconds

# ...
def exitt():
    global df
    if df is not None:
        Afile = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        df.to_csv(f'Attendance_{Afile}.csv', index=False)
        df = None
    window.destroy()
    
      



frame = tk.Frame(window, bg="#e6f5ff")
label = tk.Label(frame, text="Attendance System", font=("Arial", 22, 'bold'), fg='#4db8ff', bg="#e6f5ff")
label.grid(row=0, column=0, pady=20, padx=20)

button_start = tk.Button(frame, text="Start", width=25, height=2, command=startt, font=("Arial", 14), bg="#99d6ff")
button_start.grid(row=1, column=0, pady=20, padx=20)

button_register = tk.Button(frame, text="Register", width=25, height=2, command=open_new_window, font=("Arial", 14), bg="#99d6ff")
button_register.grid(row=2, column=0, pady=20, padx=20)

button_exit = tk.Button(frame, text="Exit", width=25, height=2, font=("Arial", 14), command=exitt, bg="#99d6ff")
button_exit.grid(row=3, column=0, pady=20, padx=20)

frame.pack()

# Start the Tkinter event loop
window.mainloop()
