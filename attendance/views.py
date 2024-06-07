import csv
from datetime import datetime
import os
import logging
import time
from turtle import pd
from venv import logger
import cv2
from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from attendance.forms import  StudentForm
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from django.core.files.base import ContentFile
from attendance.models import Attendance
from attendance_management import settings
import mysql.connector

#########################################################################################################

def capture_images(request):
    return render(request, 'capture.html')


def assure_path_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def check_haarcascadefile():
    exists = os.path.isfile("haarcascade_frontalface_default.xml")
    if exists:
        # TrackImages()
        pass
    else:
        print('please contact us')



def insert_register_to_db(student_id, name,serial):
    database = mysql.connector.connect(host='localhost', password='Ajay@2002', user='root', database='attendancedb')
    
    cursor = database.cursor()

    sql = "INSERT INTO attendance (ID, Name,serial) VALUES (%s, %s, %s)"
    check_data = "SELECT * FROM attendance WHERE ID = %s"

    try:
        cursor.execute(check_data, (student_id,))
        result = cursor.fetchone()

        if result:
            # If record exists, do not insert duplicate data
            print("Duplicate record, not inserting.")
            return "Duplicate data, already inserted."
        else:
            # If record does not exist, insert the new record
            cursor.execute(sql, (student_id,name,serial))
            database.commit()
            print("Record inserted successfully.")
            return "Record inserted successfully."
    except mysql.connector.Error as err:
        print("Error:", err)
        database.rollback()
        return f"Error: {err}"
    finally:
        cursor.close()
        database.close()
        
#################################################################################################

def take_old(name, student_id, date, time):
    database = mysql.connector.connect(host='localhost', user='root', password='Ajay@2002', database='attendancedb')
    cursor = database.cursor()

    sql = "INSERT INTO attendancedone (ID, Name, date, time) VALUES (%s, %s, %s, %s)"
    check_data = "SELECT * FROM attendancedone WHERE ID = %s AND date = %s"

    try:
        cursor.execute(check_data, (student_id, date))
        result = cursor.fetchone()

        if result:
            #record is there it does not allow duplicates............................
            print("Duplicate record, not inserting.")
            return "Duplicate data, already inserted."
        else:
            # record wasc new data is allow to store database...............
            cursor.execute(sql, (student_id, name, date, time))
            database.commit()
            print("Record inserted successfully.")
            return "Record inserted successfully."
    except mysql.connector.Error as err:
        print("Error:", err)
        database.rollback()
        return f"Error: {err}"
    finally:
        cursor.close()
        database.close()




@csrf_exempt
def register(request):
    message = request.GET.get('message', '') 
    check_haarcascadefile()
    columns = ['SERIAL NO.', '', 'ID', '', 'NAME']
    assure_path_exists("StudentDetails/")
    assure_path_exists("TrainingImage/")
    
    serial = 0
    file_path = "StudentDetails/StudentDetails.csv"
    exists = os.path.isfile(file_path)
    
    if exists:
        with open(file_path, 'r') as csvFile:
            reader = csv.reader(csvFile)
            for _ in reader:
                serial += 1
        serial = (serial // 2)
    else:
        with open(file_path, 'a+') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow(columns)
            serial = 1

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student_id = form.cleaned_data['student_id']
            name = form.cleaned_data['name']

            if name.isalpha() or ' ' in name:
                row = [serial, '', student_id, '', name]
                with open(file_path, 'a+') as csvFile:
                    writer = csv.writer(csvFile)
                    writer.writerow(row)

                    db_message = insert_register_to_db(student_id,name,serial)
                    message = f"Your {student_id} and {name} created successfully, and photo saved! {db_message}"    

                message = f"Your {student_id} and {name} created successfully, and photo saved!"

                return render(request, 'register_page.html', {'form': form, 'message': message})    
            else:
                return JsonResponse({'status': 'error', 'message': 'Enter Correct Name'})
    else:
        form = StudentForm()

    return render(request, 'register_page.html', {'form': form, 'message': message})


def attendance(request):
    return render(request, 'attendance_page.html')


"""@csrf_exempt
def save_image(request):
    if request.method == 'POST':
        try:
            # Validate the incoming POST data
            student_id = request.POST.get('student_id')
            name = request.POST.get('name')
            image_data = request.POST.get('image')
            
            if not all([student_id, name, image_data]):
                return JsonResponse({"error": "Missing required fields."}, status=400)
            
            # Sanitize student_id and name to prevent directory traversal
            student_id = re.sub(r'[^a-zA-Z0-9_-]', '', student_id)
            name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
            
            # Extract the base64 image data
            image_data = re.sub(r'^data:image/\w+;base64,', '', image_data)
            try:
                image_data = base64.b64decode(image_data)
            except base64.binascii.Error as e:
                return JsonResponse({"error": "Invalid base64 image data."}, status=400)
            
            # Define the image save path
            image_path = os.path.join("TrainingImage", f"{student_id}_{name}.jpg")
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            # Save the image
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return JsonResponse({"message": "Image saved successfully."}, status=200)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400) """


def video_stream():
    cam = cv2.VideoCapture(0)
    harcascadePath = "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(harcascadePath)

    while True:
        ret, img = cam.read()
        if not ret:
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', img)
        frame = jpeg.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    cam.release()

def video_feed(request):
    return StreamingHttpResponse(video_stream(),
                                 content_type='multipart/x-mixed-replace; boundary=frame')



logger = logging.getLogger(__name__)

@csrf_exempt
def capture_image(request):
    if request.method == 'POST':
        try:
            image_data = request.POST.get('image')
            count = request.POST.get('count')
            serial = request.POST.get('serial')
            student_id = request.POST.get('student_id')
            name = request.POST.get('name')

            if image_data and count is not None and serial and student_id and name:
                # Check if the student has already marked attendance
                from .models import Attendance  # Adjust the import according to your project structure

                attendance_record = Attendance.objects.filter(student_id=student_id, date=datetime.date.today()).first()
                if attendance_record:
                    return JsonResponse({'status': 'attended', 'message': 'Attendance already recorded'})

                directory = "TrainingImage/"
                if not os.path.exists(directory):
                    os.makedirs(directory)
                img_data = base64.b64decode(image_data)
                img_name = f"{directory}/{name}.{serial}.{student_id}.{count}.jpg"
                with open(img_name, 'wb') as f:
                    f.write(img_data)

                logger.debug(f"Image saved successfully: {img_name}")
                # Record the attendance in the database
                Attendance.objects.create(student_id=student_id, name=name, image_path=img_name)

                return JsonResponse({'status': 'success'})
            else:
                logger.error("Missing parameters in the POST request")
                return JsonResponse({'status': 'failure', 'message': 'Missing parameters'})
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return JsonResponse({'status': 'failure', 'message': str(e)})
    else:
        return JsonResponse({'status': 'failure', 'message': 'Invalid request method'})


assure_path_exists("attendance_details/")
file_path = "attendance_details/attendance.csv"
exists = os.path.isfile(file_path)
if not exists:
    with open(file_path, 'a+') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(['Name', 'Student ID', 'Date', 'Time', 'Image Filename'])





@csrf_exempt
def track_images(request):
    if request.method == 'POST':
        try:
            image_data = request.POST.get('image')
            name = request.POST.get('name')
            student_id = request.POST.get('id')
            datetime_str = request.POST.get('datetime')

            # Handle the 'Z' at the end of the datetime string
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1]
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')
            else:
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f')

            # Ensure the attendance directory exists
            assure_path_exists("attendance_details/")

            # Decode the image
            image_binary = base64.b64decode(image_data)
            image_filename = f"{student_id}_{datetime_obj.strftime('%Y%m%d_%H%M%S')}.jpg"
            image_path = os.path.join("attendance_details/", image_filename)

            # Check for duplicates in the CSV file
            with open(file_path, mode='r', newline='') as file:
                reader = csv.reader(file)
                for row in reader:
                    if len(row) < 3:
                        continue  # Skip any malformed or incomplete rows
                    if row[1] == student_id and row[2] == datetime_obj.date().isoformat():
                        print(f"Duplicate entry found for student ID {student_id} on {datetime_obj.date().isoformat()}")
                        return JsonResponse({'status': 'duplicate'})

            # Save the image
            with open(image_path, 'wb') as f:
                f.write(image_binary)
            print(f"Image saved: {image_path}")

            # Save the attendance details to CSV
            with open(file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([name, student_id, datetime_obj.date().isoformat(), datetime_obj.time().isoformat(), image_filename])
            print(f"Attendance details saved for student ID {student_id}")
            
            date = datetime_obj.date().isoformat()
            time = datetime_obj.time().isoformat()
            result = take_old(name, student_id, date, time)
            print(result)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'status': 'failed', 'error': str(e)})

    return JsonResponse({'status': 'failed'})
