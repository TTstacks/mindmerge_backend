from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from users.serializers import UserRegistrationSerializer, UserSerializer, SchoolSerializer, UserReadSerializer, UserImageSerializer
from users.models import School
from users.utilities import get_tokens_for_user
from users.permissions import UpdateOwn
from backend.settings import AGORA_APP_ID, AGORA_APP_CERTIFICATE, AGORA_HOST, AGORA_ORG_NAME, AGORA_APP_NAME, SUPABASE_KEY, SUPABASE_URL
from supabase import create_client, AuthError

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Create your views here.
class LoginView(APIView):

    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        user = authenticate(email = email, password = password)
        if user:
            return Response(data = get_tokens_for_user(user))

        return Response(status = status.HTTP_401_UNAUTHORIZED)

class SignupView(APIView):

    def post(self, request):


        email = request.data.get("email")
        password = request.data.get("password")




        userRegistrationSerializer = UserRegistrationSerializer(data = request.data)
        userRegistrationSerializer.is_valid(raise_exception=True)

        try:
            response = supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True
            })

        except AuthError as e:
            return Response(
                data=e.message,
                status=e.status
            )
        
        try:
            user = userRegistrationSerializer.save(supabase_uid = response.user.id)
        except School.DoesNotExist:
            return Response(status = status.HTTP_400_BAD_REQUEST)
        
        
        return Response(data = get_tokens_for_user(user))

class UserView(RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    permission_classes = [IsAuthenticated, UpdateOwn]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserReadSerializer
        return UserSerializer
    
    def get_object(self):

        if self.lookup_field in self.kwargs:
            filter_kwargs = {self.lookup_field: self.kwargs[self.lookup_field]}
            obj = get_object_or_404(self.get_queryset(), **filter_kwargs)
        else:
            obj = self.request.user

        self.check_object_permissions(self.request, obj)

        return obj
    


class UserUploadImageView(APIView):
    permission_classes=[IsAuthenticated, UpdateOwn]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        userImageSerializer = UserImageSerializer(request.user.student, data = request.data)
        userImageSerializer.is_valid(raise_exception=True)
        userImageSerializer.save()
        userReadSerializer = UserReadSerializer(request.user)
        return Response(data = userReadSerializer.data)


class SchoolView(ListAPIView):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = []
