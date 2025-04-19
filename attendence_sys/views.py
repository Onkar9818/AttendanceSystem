from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import Student, Attendence
from .filters import AttendenceFilter

# from django.views.decorators import gzip

from .recognizer import Recognizer
from datetime import date

@login_required(login_url = 'login')
def home(request):
    studentForm = CreateStudentForm()

    if request.method == 'POST':
        studentForm = CreateStudentForm(data = request.POST, files=request.FILES)
        # print(request.POST)
        stat = False 
        try:
            student = Student.objects.get(registration_id = request.POST['registration_id'])
            stat = True
        except:
            stat = False
        if studentForm.is_valid() and (stat == False):
            studentForm.save()
            name = studentForm.cleaned_data.get('firstname') +" " +studentForm.cleaned_data.get('lastname')
            messages.success(request, 'Student ' + name + ' was successfully added.')
            return redirect('home')
        else:
            messages.error(request, 'Student with Registration Id '+request.POST['registration_id']+' already exists.')
            return redirect('home')

    context = {'studentForm':studentForm}
    return render(request, 'attendence_sys/home.html', context)


def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username or Password is incorrect')

    context = {}
    return render(request, 'attendence_sys/login.html', context)

@login_required(login_url = 'login')
def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url = 'login')
def updateStudentRedirect(request):
    context = {}
    if request.method == 'POST':
        try:
            reg_id = request.POST['reg_id']
            branch = request.POST['branch']
            student = Student.objects.get(registration_id = reg_id, branch = branch)
            updateStudentForm = CreateStudentForm(instance=student)
            context = {'form':updateStudentForm, 'prev_reg_id':reg_id, 'student':student}
        except:
            messages.error(request, 'Student Not Found')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)

@login_required(login_url = 'login')
def updateStudent(request):
    if request.method == 'POST':
        context = {}
        try:
            student = Student.objects.get(registration_id = request.POST['prev_reg_id'])
            updateStudentForm = CreateStudentForm(data = request.POST, files=request.FILES, instance = student)
            if updateStudentForm.is_valid():
                updateStudentForm.save()
                messages.success(request, 'Updation Success')
                return redirect('home')
        except:
            messages.error(request, 'Updation Unsucessfull')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)


@login_required(login_url='login')
def takeAttendence(request):
    if request.method == 'POST':
        details = {
            'branch': request.POST['branch'],
            'year': request.POST['year'],
            'section': request.POST['section'],
            'period': request.POST['period'],
            'faculty': request.user.faculty
        }
        
        # Check if attendance already exists
        today = date.today()
        existing = Attendence.objects.filter(
            date=today,
            branch=details['branch'],
            year=details['year'],
            section=details['section'],
            period=details['period']
        ).exists()
        
        if existing:
            messages.error(request, "Attendance already recorded for this class/period.")
            return redirect('home')
        
        try:
            # Get recognized student IDs
            recognized_ids = Recognizer(details)
            
            # Get all students for this class
            students = Student.objects.filter(
                branch=details['branch'],
                year=details['year'],
                section=details['section']
            )
            
            # Create attendance records
            attendance_records = []
            for student in students:
                status = 'Present' if str(student.registration_id) in recognized_ids else 'Absent'
                attendance_records.append(
                    Attendence(
                        Faculty_Name=str(request.user.faculty),
                        Student_ID=str(student.registration_id),
                        period=details['period'],
                        branch=details['branch'],
                        year=details['year'],
                        section=details['section'],
                        status=status
                    )
                )
            
            # Bulk create for efficiency
            Attendence.objects.bulk_create(attendance_records)
            
            # Get the newly created records for display
            attendances = Attendence.objects.filter(
                date=today,
                branch=details['branch'],
                year=details['year'],
                section=details['section'],
                period=details['period']
            )
            
            messages.success(request, f"Attendance recorded successfully! Present: {len(recognized_ids)}/{students.count()}")
            context = {
                "attendences": attendances,
                "ta": True,
                "class_info": f"{details['branch']} {details['year']}-{details['section']} Period {details['period']}"
            }
            return render(request, 'attendence_sys/attendence.html', context)
            
        except Exception as e:
            messages.error(request, f"Error taking attendance: {str(e)}")
            return redirect('home')
    
    return render(request, 'attendence_sys/home.html')

def searchAttendence(request):
    attendences = Attendence.objects.all()
    myFilter = AttendenceFilter(request.GET, queryset=attendences)
    attendences = myFilter.qs
    context = {'myFilter':myFilter, 'attendences': attendences, 'ta':False}
    return render(request, 'attendence_sys/attendence.html', context)


def facultyProfile(request):
    faculty = request.user.faculty
    form = FacultyForm(instance = faculty)
    context = {'form':form}
    return render(request, 'attendence_sys/facultyForm.html', context)



# class VideoCamera(object):
#     def __init__(self):
#         self.video = cv2.VideoCapture(0)
#     def __del__(self):
#         self.video.release()

#     def get_frame(self):
#         ret,image = self.video.read()
#         ret,jpeg = cv2.imencode('.jpg',image)
#         return jpeg.tobytes()


# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield(b'--frame\r\n'
#         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# @gzip.gzip_page
# def videoFeed(request):
#     try:
#         return StreamingHttpResponse(gen(VideoCamera()),content_type="multipart/x-mixed-replace;boundary=frame")
#     except:
#         print("aborted")

# def getVideo(request):
#     return render(request, 'attendence_sys/videoFeed.html')