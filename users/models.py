from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from .utilities import safe_file_name, SafeFileName

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, middle_name, last_name, password = None):
        if not email:
            raise ValueError("users must have email")
        
        if not first_name:
            raise ValueError("users must have a name")

        if not last_name:
            raise ValueError("users must have a last name")

        user = self.model(
            email = self.normalize_email(email),
            first_name = first_name,
            middle_name = middle_name,
            last_name = last_name,
        )

        user.set_password(password)
        user.save(using = self._db)
        return user

    def create_superuser(self, email, first_name, middle_name, last_name, password=None):
        user = self.create_user(email, first_name, middle_name, last_name, password)
        user.is_admin = True
        user.save(using = self._db)
        return user


class User(AbstractBaseUser):
    supabase_uid = models.CharField(max_length=255, unique=True)
    email = models.EmailField(max_length = 255, unique=True)
    first_name = models.CharField(max_length=255)
    middle_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default = False)
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        return self.email
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    

class School(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE, primary_key=True)
    grade = models.CharField(max_length=3, validators=[
        RegexValidator(
            regex=r'^(?:[7-9]|1[0-2])[A-Z]$',
            message='enter a grade in a 11A format',
        ),
    ])
    description = models.TextField(default="")
    school = models.ForeignKey(School, on_delete = models.CASCADE)
    image = models.ImageField(upload_to=safe_file_name('users'), default='users/default.jpg')