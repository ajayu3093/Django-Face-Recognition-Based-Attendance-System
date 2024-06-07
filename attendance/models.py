from django.db import models
import datetime

class Student(models.Model):
    student_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

class Image(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='TrainingImage/')
    created_at = models.DateTimeField(auto_now_add=True)
    
class Attendance(models.Model):
    #id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    student_id = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    image_path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.student_id} - {self.date}"

class Meta:
    unique_together = ('student_id','date')


