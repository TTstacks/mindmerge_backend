from rest_framework.test import APITransactionTestCase
from django.contrib.auth import get_user_model
from users.models import Student, School
import random
import json
from users.urls import urlpatterns
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Create your tests here.
class AccountTestCase(APITransactionTestCase):
    reset_sequences=True
    def setUp(self):
        self.create_schools()
        self.create_users()
        self.apiUrl = 'http://127.0.0.1:8000/api'
        self.accessUserA, self.refreshUserA = self.login('a')
        self.accessUserB, self.refreshUserB = self.login('b')
        self.accessUserC, self.refreshUserC = self.login('c')
        self.accessUserD, self.refreshUserD = self.login('d')

    def test_create_account(self):
        print(urlpatterns)
        data = {
            "email": "gg@gg.com",
            "full_name": "   Fake    Name",
            "password": "request",
            "password2": "request",
            "student": {
                "grade": " 8  B ",
                "school": "NIS1",
            },
        }
        self.request_post('signup', None, data= json.dumps(data))
        self.request_post('login', None, data = json.dumps({'email': 'gg@gg.com', 'password': 'request'}))


        edit_data = {
            'student': {
                'grade': '10B'
            }
        }
        self.request_get('user/1/', self.accessUserB)
        self.request_get('user/', self.accessUserB)
        self.request_patch('user/2/', self.accessUserB, data = json.dumps(edit_data))
        edit_data = {
            'student': {
                'grade': '11B'
            }
        }
        self.request_patch('user/', self.accessUserB, data = json.dumps(edit_data))
        self.request_get('user/1/', self.accessUserB)
        print(self.refreshUserA)
        self.request_post('token/refresh/', None, data = json.dumps({'refresh': self.refreshUserA}))
        
    def test_image(self):
        image_data = BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(image_data, format='png')
        image_data.seek(0)
        response = self.client.post(f'{self.apiUrl}/user/image/', data={'image': SimpleUploadedFile("test.png", image_data.read(), content_type='image/png')}, format='multipart', 
            headers=self.set_headers_request(
                self.accessUserA
        ))
        print(response.content, response.data)
        self.assertEqual(response.status_code, 200)

        self.request_get('user/1/', self.accessUserA)
        

    def request_post(self, url_part, access, data, need_print = True, code = 200):
        response = self.client.post(f'{self.apiUrl}/{url_part}', data = data, content_type='application/json', headers=self.set_headers_request(access))
        if need_print:
            print(response.data)
        self.assertEqual(response.status_code, code)
    
    def request_get(self, url_part, access, need_print=True, code = 200):
        response = self.client.get(f'{self.apiUrl}/{url_part}', content_type='application/json', headers=self.set_headers_request(access))
        if need_print:
            print(response.data)
        self.assertEqual(response.status_code, code)

    def request_patch(self, url_part, access, data, need_print=True, code = 200):
        response = self.client.patch(f'{self.apiUrl}/{url_part}', data = data, content_type='application/json', headers=self.set_headers_request(access))
        if need_print:
            print(response.content)
        self.assertEqual(response.status_code, code)
    
    def request_delete(self, url_part, access, need_print = True, code = 200):
        response = self.client.delete(f'{self.apiUrl}/{url_part}', content_type='application/json', headers=self.set_headers_request(access))
        if need_print:
            print(response.errors)
        self.assertEqual(response.status_code, code)

    
    def create_schools(self):
        for i in range(1, 11):
            School.objects.create(name = f'NIS{i}')

    def create_users(self):
        for i in range(ord('a'), ord('d') + 1):
            c = chr(i)
            u = get_user_model().objects.create(email = f'{c}@{c}.com', first_name = c, last_name = c, middle_name = c)
            u.set_password(c)
            u.save()
            st = Student.objects.create(user = u, school = School.objects.get(name = f'NIS{random.randint(1, 10)}'), grade = self.generate_random_grade())

    def generate_random_grade(self):
        random_number = random.randint(7, 12)
        random_letter = chr(random.randint(ord('A'), ord('Z')))
        return f'{random_number}{random_letter}'


    def login_data(self, letter):
        data = {'email': f'{letter}@{letter}.com', 'password': letter}
        return data
    
    def login(self, letter):
        response = self.client.post(f'{self.apiUrl}/login', data = self.login_data(letter))
        self.assertEqual(response.status_code, 200)
        return [response.data.get('access'), response.data.get('refresh')]
    
    def set_headers_request(self, access):

        return {'Authorization': f'Bearer {access}'} if access else {}
        
