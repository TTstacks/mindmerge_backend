from rest_framework import serializers
from django.contrib.auth import get_user_model
from users.models import Student, User, School
from users.utilities import extract_names, get_grade

class StudentSerializer(serializers.ModelSerializer):
    school = serializers.SlugRelatedField(queryset = School.objects.all(), slug_field='name')

    class Meta:
        model = Student
        fields = ['school', 'grade', 'image']
        read_only_fields = ['image']

    def to_internal_value(self, data):
        if 'grade' in data:
            try:
                data['grade'] = get_grade(data['grade'])
            except ValueError:
                raise serializers.ValidationError('incorrect grade format')
        return super().to_internal_value(data)

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    student = StudentSerializer()

    class Meta:
        model = User
        fields = ['first_name', 'middle_name', 'last_name', 'student']
    
    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.middle_name = validated_data.get('middle_name', instance.middle_name)
        student_data = validated_data.pop('student', None)
        if student_data:
            student = instance.student
            student.school = student_data.get('school', student.school)
            student.grade = student_data.get('grade', student.grade)
            student.description = student_data.get('description', student.description)
            student.save()
        
        return instance
    
    def to_internal_value(self, data):
        if 'full_name' in data:
            data['last_name'], data['first_name'], data['middle_name'] = extract_names(data.pop('full_name'))
        return super().to_internal_value(data)
    
class UserImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['image']

class UserReadSerializer(serializers.ModelSerializer):
    student = StudentSerializer(many = False, read_only = True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'middle_name', 'last_name', 'student',]

class UserShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['first_name', 'middle_name', 'last_name']


class UserRegistrationSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    password2 = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'middle_name', 'last_name', 'password', 'password2', 'student']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('password2')
        student_data = validated_data.pop('student')
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save()
        student = Student(user = user, **student_data)
        student.save()
        return user
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('passwords do not match')
        return attrs
    
    def to_internal_value(self, data):
        try:
            data['last_name'], data['first_name'], data['middle_name'] = extract_names(data.pop('full_name', None))
        except ValueError:
            raise serializers.ValidationError('incorrect naming format')
        return super().to_internal_value(data)