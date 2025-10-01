from rest_framework.test import APITransactionTestCase
from django.contrib.auth import get_user_model
from users.models import Student, School
from projects.models import Project, Tag
from enum import IntEnum
import random
import json
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

class RequestEnum(IntEnum):
    POST=1
    GET=2
    PATCH=3
    DELETE=4

# Create your tests here.
class ProjectTest(APITransactionTestCase):
    reset_sequences=True

    def setUp(self):
        Tag.objects.create(name = 'Physics')
        Tag.objects.create(name = 'Biology')
        Tag.objects.create(name = 'Chemistry')
        Tag.objects.create(name = 'Philosophy')
        self.create_schools()
        self.create_users()
        for user in get_user_model().objects.all():
            self.create_project(user)
        self.apiUrl = 'http://127.0.0.1:8000/api'
        self.accessUserA = self.login('a')
        self.accessUserB = self.login('b')
        self.accessUserC = self.login('c')
        self.accessUserD = self.login('d')
        Project.objects.get(id = 1).tags.add(Tag.objects.get(id = 3))
        pr = Project.objects.get(id = 1)
        pr.title = 'its party'
        pr.save()


    def test_membership(self):

        self.handle_request_methods(RequestEnum.GET, 'project/2/', self.accessUserA,)

        self.handle_request_methods(RequestEnum.POST, 'project/2/membership/', self.accessUserA, data = self.membership_join_data('may I join'))
        self.handle_request_methods(RequestEnum.POST, 'project/2/membership/', self.accessUserC, data = self.membership_join_data('may I join too?'))
        self.handle_request_methods(RequestEnum.POST, 'project/2/membership/', self.accessUserB, data = self.membership_join_data('I want to join'), code=403)
        self.handle_request_methods(RequestEnum.POST, 'project/2/membership/', self.accessUserD, data = self.membership_join_data('join me, for I have experience'))

        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/', self.accessUserB)

        self.handle_request_methods(RequestEnum.PATCH, 'project/2/membership/2/', self.accessUserB, data = {'status': 2})
        self.handle_request_methods(RequestEnum.PATCH, 'project/2/membership/3/', self.accessUserB, data = {'status': 2})
        self.handle_request_methods(RequestEnum.PATCH, 'project/2/membership/3/', self.accessUserC, data = {'status': 2}, code = 403)

        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/2/', self.accessUserB)
        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/1/', self.accessUserB)

        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/2/', self.accessUserA)
        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/1/', self.accessUserA, code = 404)

        self.handle_request_methods(RequestEnum.GET, 'project/2/', self.accessUserA,)

        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/2/', self.accessUserB)
        self.handle_request_methods(RequestEnum.DELETE, 'project/2/', self.accessUserC)
        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/', self.accessUserC)
        self.handle_request_methods(RequestEnum.GET, 'project/2/membership/', self.accessUserB)

    def test_tags(self):
        self.handle_request_methods(RequestEnum.GET, 'tags/?name=P', self.accessUserA)
    
    def test_project(self):
        self.handle_request_methods(RequestEnum.PATCH, 'project/1/', self.accessUserA, data={'tags': ['Physics', 'Biology']})
        self.handle_request_methods(RequestEnum.PATCH, 'project/1/', self.accessUserA, data = {'title': 'party'})
        self.handle_request_methods(RequestEnum.GET, 'tags/?name=P', self.accessUserA)
        self.handle_request_methods(RequestEnum.PATCH, 'project/2/', self.accessUserB, data = {'tags': ['Philosophy']})
        self.handle_request_methods(RequestEnum.PATCH, 'project/3/', self.accessUserC, data = {'tags': ['Philosophy']})
        self.handle_request_methods(RequestEnum.GET, 'tags/?name=P', self.accessUserA)
        self.handle_request_methods(RequestEnum.PATCH, 'project/3/', self.accessUserC, data = {'tags': ['Biology']})
        self.handle_request_methods(RequestEnum.GET, 'project/?tags=Physics,Biology', self.accessUserA)
        self.handle_request_methods(RequestEnum.GET, 'project/?search_for=d', self.accessUserA)

    def test_user_project(self):
        self.handle_request_methods(RequestEnum.POST, 'project/1/membership/', self.accessUserB, data = self.membership_join_data('we should be together'))
        self.handle_request_methods(RequestEnum.POST, 'project/1/membership/', self.accessUserC, data = self.membership_join_data('pick me user B is not it'))
        self.handle_request_methods(RequestEnum.GET, 'user/2/projects/', self.accessUserB)
        self.handle_request_methods(RequestEnum.PATCH, 'project/1/membership/1/', self.accessUserA, data = {'status': 2})
        self.handle_request_methods(RequestEnum.GET, 'user/2/projects/', self.accessUserB)
        self.handle_request_methods(RequestEnum.POST, 'project/3/membership/', self.accessUserB, data = self.membership_join_data('please can I join'))
        self.handle_request_methods(RequestEnum.PATCH, 'project/3/membership/3/', self.accessUserC, data = {'status': 3})
        self.handle_request_methods(RequestEnum.GET, 'user/2/projects/', self.accessUserB)
        self.handle_request_methods(RequestEnum.GET, 'user/2/projects/', self.accessUserB)
        self.handle_request_methods(RequestEnum.GET, 'project/1/membership/1/', self.accessUserA)
        self.handle_request_methods(RequestEnum.PATCH, 'project/1/', self.accessUserA, data={'privacy': 2})
        self.handle_request_methods(RequestEnum.GET, 'project/?search_for=d', self.accessUserB)
        self.handle_request_methods(RequestEnum.GET, 'project/?search_for=d', self.accessUserC)
        self.handle_request_methods(RequestEnum.GET, 'project/?search_for=d', self.accessUserD)

    def test_image(self):
        self.handle_request_methods(RequestEnum.GET, 'project/1/', self.accessUserA)

    def handle_request_methods(self, request_code, url_part, access, data={}, need_print=True, code=200):
        json_data = json.dumps(data)

        match request_code:
            case RequestEnum.POST:
                response = self.client.post(f'{self.apiUrl}/{url_part}', data = json_data, content_type='application/json', headers=self.set_request_headers(access))        
            case RequestEnum.GET:
                response = self.client.get(f'{self.apiUrl}/{url_part}', content_type='application/json', headers=self.set_request_headers(access))        
            case RequestEnum.PATCH:
                response = self.client.patch(f'{self.apiUrl}/{url_part}', data = json_data, content_type='application/json', headers=self.set_request_headers(access))
            case RequestEnum.DELETE:
                response = self.client.delete(f'{self.apiUrl}/{url_part}', content_type='application/json', headers=self.set_request_headers(access))
            case _:
                raise ValueError('Error')
        
        
        self.assertEqual(response.status_code, code)

    def create_schools(self):
        for i in range(RequestEnum.POST, 11):
            School.objects.create(name = f'NIS{i}')

    def create_users(self):
        for i in range(ord('a'), ord('d') + 1):
            c = chr(i)
            u = get_user_model().objects.create(email = f'{c}{c}{c}@{c}{c}{c}.com', first_name = c, last_name = c, middle_name = c, supabase_uid = f'{c}{c}{c}')
            u.set_password(c)
            u.save()
            st = Student.objects.create(user = u, school = School.objects.get(name = f'NIS{random.randint(RequestEnum.POST, 10)}'), grade = self.generate_random_grade())

    def generate_random_grade(self):
        random_number = random.randint(7, 12)
        random_letter = chr(random.randint(ord('A'), ord('Z')))
        return f'{random_number}{random_letter}'

    def create_project(self, user):
        p = Project.objects.create(admin = user, title = f'{user.first_name}\'s project', description = f'{user.first_name} is cool')
    

    def membership_join_data(self, text):
        return {'join_request_text': text}
    
    def login_data(self, letter):
        data = {'email': f'{letter}{letter}{letter}@{letter}{letter}{letter}.com', 'password': letter}
        return data
    
    def login(self, letter):
        response = self.client.post(f'{self.apiUrl}/login', data = self.login_data(letter))
        self.assertEqual(response.status_code, 200)
        return response.data.get('access')

    def set_request_headers(self, access):
        return {'Authorization': f'Bearer {access}'}