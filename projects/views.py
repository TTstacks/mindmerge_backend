from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db import transaction
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework import status
from projects.serializers import ProjectSerializer, ProjectReadSerializer, TagSerializer, MembershipSerializer, MembershipReadSerializer, MessageSerializer, MessageAuthorSerializer, MessageSerializerRead, ProjectSearchSerializer
from projects.models import Project, Tag, Membership, Message, WebhookEvent
from projects.permissions import IsOwner, IsMember, IsNotOwnerAndNotMember
from projects.utilities import trigger_member_event, process_agora_webhook
from rest_framework.pagination import PageNumberPagination
import pusher
import json
from common.agora_utilities.RtcTokenBuilder2 import RtcTokenBuilder, Role_Publisher
from pusher_push_notifications import PushNotifications
from backend.settings import PUSHER_APP_ID, PUSHER_CLUSTER, PUSHER_KEY, PUSHER_SECRET, BEAMS_ID, BEAMS_KEY, AGORA_APP_ID, AGORA_APP_CERTIFICATE, AGORA_RTC_EVENTS_SECRET
import hmac
import hashlib
from django.views.decorators.csrf import csrf_exempt

pusher_client = pusher.Pusher(app_id=PUSHER_APP_ID, key = PUSHER_KEY, secret=PUSHER_SECRET, cluster=PUSHER_CLUSTER, ssl = True)
beams_client = PushNotifications(instance_id=BEAMS_ID, secret_key=BEAMS_KEY)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def agora_webhook(request):

    signature = request.headers.get('Agora-Signature')

    body = request.body

    if not signature:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    digester = hmac.new(AGORA_RTC_EVENTS_SECRET.encode(), body, hashlib.sha1)
    calculated_signature = digester.hexdigest()

    if calculated_signature != signature:
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    
    notice_id = request.data.get('noticeId')
    
    with transaction.atomic():
        webhook_event, created = WebhookEvent.objects.get_or_create(idempotency_key=notice_id)

        if not created:
            return Response()
            
        event_type = request.data.get('eventType')
        payload = request.data.get('payload')
        channel_name = payload.get('channelName')

        process_agora_webhook(pusher_client, beams_client, event_type, channel_name, payload)

    return Response()



class CustomPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_query_param = 'page'

# Create your views here.
class ProjectViewSet(ModelViewSet):

    pagination_class= CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ["list", "retrieve", "create"]:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "image_upload"]:
            self.permission_classes = [IsAuthenticated, IsOwner]
        elif self.action == "destroy":
            self.permission_classes = [IsAuthenticated, IsOwner|IsMember]
        elif self.action == "membership":
            if self.request.method == "GET":
                self.permission_classes = [IsAuthenticated]
            elif self.request.method == "POST":
                self.permission_classes = [IsAuthenticated, IsNotOwnerAndNotMember]
        elif self.action == "membership_detail":
            if self.request.method == "GET":
                self.permission_classes = [IsAuthenticated]
            elif self.request.method == "PATCH":
                self.permission_classes = [IsAuthenticated, IsOwner]
        
        return [permission() for permission in self.permission_classes]
        

    def get_serializer_class(self):

        if self.action in ["list", "retrieve"]:
            return ProjectReadSerializer

        return ProjectSerializer

    def get_queryset(self):
        tags = self.request.query_params.get('tags', None)
        school = self.request.query_params.get('school', None)
        search_for = self.request.query_params.get('search_for', None)
        queryset = Project.objects.all()

        if tags is not None:
            if tags.strip() != '':
                tags_list = tags.split(',')
                tags = Tag.objects.filter(name__in = tags_list)
                queryset = queryset.filter(tags__in = tags)

        if school is not None:
            if school.strip() != '':
                school_list = school.split(',')
                queryset = queryset.filter(admin__student__school__id__in=school_list)


        if search_for is not None:
            search_vectors = (
                SearchVector('title') + 
                SearchVector('description') + 
                SearchVector('admin__first_name') + 
                SearchVector('admin__middle_name') + 
                SearchVector('admin__last_name')
            )

            
            search_query = SearchQuery(search_for)

            queryset = queryset.annotate(
                rank = SearchRank(search_vectors, search_query)
            ).order_by('-rank')


        queryset = queryset.exclude(privacy=2)



        return queryset.distinct()

    def create(self, request):
        projectSerializer = ProjectSerializer(data = request.data)
        projectSerializer.is_valid(raise_exception=True)
        project = projectSerializer.save(admin = request.user)
        projectReadSerializer = ProjectReadSerializer(project)
        return Response(data = projectReadSerializer.data)
        

    def destroy(self, request, pk=None):
        
        try:
            project = Project.objects.get(id = pk)
        except Project.DoesNotExist:
            return Response(status = status.HTTP_404_NOT_FOUND)
        
        if request.user == project.admin:
            project.delete()
            return Response()
        
        project.members.remove(request.user)
        return Response()

    @action(detail=True, methods=['post'], url_path='image', parser_classes=[FormParser, MultiPartParser])
    def image_upload(self, request, pk=None):
        project = self.get_object()
        image = request.data['image']
        project.image = image
        project.save()
        projectReadSerializer = ProjectReadSerializer(project)
        return Response(data = projectReadSerializer.data)


    @action(detail=True, methods=['get', 'post'], url_path='membership')
    def membership(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            return self.get_membership_list(request, project)
        
        return self.membership_create(request, project)
    
    def get_membership_list(self, request, project):
        membership_set = project.project_membership_set
        if project.admin != request.user:
            membership_set = membership_set.filter(Q(status = 2) | Q(user = request.user))
        
        membershipReadSerializer = MembershipReadSerializer(membership_set, many=True)
        return Response(data = membershipReadSerializer.data)

    def membership_create(self, request, project):
        user = request.user
        membershipSerializer = MembershipSerializer(data = request.data)
        membershipSerializer.is_valid(raise_exception=True)
        membership = membershipSerializer.save(user = user, project = project)
        membershipReadSerializer = MembershipReadSerializer(membership)

        projectReadSerializer =  ProjectReadSerializer(project)
        pusher_client.trigger(f'private-user-{project.admin.id}', 'member_joined', {
            'project': projectReadSerializer.data,
            'member': membershipReadSerializer.data
        })

        pusher_client.trigger(f'private-user-{membership.user.id}', 'member_joined', {
            'project': projectReadSerializer.data,
            'member': membershipReadSerializer.data
        })

        user_ids=[f'user-{project.admin.id}']

        body_string = f'{membership.user.email} sent request to join your project'

        beams_client.publish_to_users(
            user_ids=user_ids,
            publish_body={
                'web': {
                    'notification': {
                        'title': project.title,
                        'body': body_string,
                        'icon': project.image.url,
                        "deep_link": f'http://localhost:4200/project/{project.id}'
                    }
                }
            }
        )


        return Response(data = membershipReadSerializer.data)
    
    @action(detail=True, methods=['get', 'patch'], url_path=r'membership/(?P<membership_pk>[^/.]+)')
    def membership_detail(self, request, pk=None, membership_pk = None):
        project = self.get_object()
        if request.method == 'GET':
            return self.get_membership_detail_unit(request, project, membership_pk)
        
        return self.membership_detail_patch(request, project, membership_pk)

    def get_membership_detail_unit(self, request, project, membership_pk):
        membership_set = project.project_membership_set
        if project.admin != request.user:
            membership_set = membership_set.filter(status = 2)
        
        try:
            membership = membership_set.get(id = membership_pk)
        except:
            return Response(status = status.HTTP_404_NOT_FOUND)

        membershipReadSerializer = MembershipReadSerializer(membership)
        return Response(data = membershipReadSerializer.data)
    
    def membership_detail_patch(self, request, project, membership_pk):

        try:
            membership = project.project_membership_set.get(id = membership_pk)
        except Membership.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user = request.user

        previous_status = membership.status

        membershipSerializer = MembershipSerializer(instance = membership, data = request.data, partial=True)
        membershipSerializer.is_valid(raise_exception=True)
        membership = membershipSerializer.save()

        membershipReadSerializer = MembershipReadSerializer(membership)
        projectReadSerializer = ProjectReadSerializer(project)

        accepted_members = project.members.exclude(id=membership.user.id).filter(user_membership_set__status=2).distinct()

        current_status = membership.status

        event_name = 'member_joined' if current_status == 2 else 'member_kicked'
        
        user_ids = []

        if previous_status == 1:
            trigger_member_event(pusher_client, f'private-user-{project.admin.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
            trigger_member_event(pusher_client, f'private-user-{membership.user.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
            user_ids.append(f'user-{membership.user.id}')
            if current_status == 2:
                for member in accepted_members:
                    trigger_member_event(pusher_client, f'private-user-{member.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
                    user_ids.append(f'user-{member.id}')
        else:
            trigger_member_event(pusher_client, f'private-user-{project.admin.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
            trigger_member_event(pusher_client, f'private-user-{membership.user.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
            user_ids.append(f'user-{membership.user.id}')
            for member in accepted_members:
                trigger_member_event(pusher_client, f'private-user-{member.id}', event_name, projectReadSerializer.data, membershipReadSerializer.data)
                user_ids.append(f'user-{member.id}')
        

        if current_status == 2:
            body_text = f"{membership.user.email} joined the project"
        else:
            body_text = f"{membership.user.email} got kicked out of the project"

        beams_client.publish_to_users(
            user_ids=user_ids,
            publish_body={
                'web': {
                    'notification': {
                        'title': project.title,
                        'body': body_text,
                        'icon': project.image.url,
                        "deep_link": f'http://localhost:4200/project/{project.id}'
                    }
                }        
            }
        )


        return Response(data = membershipSerializer.data)


    @action(detail = True, methods = ['get', 'post'], url_path='message', parser_classes=[FormParser, MultiPartParser], permission_classes=[IsAuthenticated, IsMember | IsOwner])
    def message(self, request, pk=None):
        project = self.get_object()
        if request.method == 'GET':
            return self.get_messages(request, project)
        
        return self.create_message(request, project)
        
    def get_messages(self, request, project):
        messages = Message.objects.filter(project__id = project.id).order_by('-id')[:20:-1]
        messages_serializer = MessageSerializerRead(messages, many=True)
        return Response(data = messages_serializer.data)

    def create_message(self, request, project):
        
        user = request.user
        messageSerializer = MessageSerializer(data = request.data)
        messageSerializer.is_valid(raise_exception=True)
        message = messageSerializer.save(user = user, project = project)
        messageReadSerializer = MessageSerializerRead(instance = message)

        channel_name = f"private-project-{project.id}"
        a = pusher_client.trigger(u'%s' % channel_name, u'message_sent', messageReadSerializer.data)

        projectReadSerializer = ProjectReadSerializer(project)

        
        self.trigger_user_channel(project.admin.id, projectReadSerializer.data, messageReadSerializer.data)
        for member in project.members.all():
            self.trigger_user_channel(member.id, projectReadSerializer.data, messageReadSerializer.data)
        

        return Response(data = messageReadSerializer.data)
    
    @action(detail=False, methods=['post'], url_path='pusher/auth', permission_classes=[IsAuthenticated])
    def pusher_authorize(self, request):
        channel_name = request.data['channel_name']
        socket_id = request.data['socket_id']
        user = request.user

        if channel_name.find('private-project-') != -1:
            return self.pusher_authorize_project(channel_name, socket_id, user)
        elif channel_name.find('private-user-') != -1:
            return self.pusher_authorize_user(channel_name, socket_id, user)
        
        return Response(status=status.HTTP_403_FORBIDDEN)
    

    def pusher_authorize_admin(self, channel_name, socket_id, user):
        project_id = int(channel_name.removeprefix('private-admin-'))

        try:
            project = Project.objects.get(id=project_id)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if user.id != project.admin.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        auth = pusher_client.authenticate(
            channel = channel_name,
            socket_id=socket_id
        )
        return Response(data=auth)
    
    def pusher_authorize_project(self, channel_name, socket_id, user):
        project_id = int(channel_name.removeprefix('private-project-'))

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        if project.admin == user or project.members.through.objects.filter(status=2, user=user, project=project).exists():
            auth = pusher_client.authenticate(
                channel=channel_name,
                socket_id=socket_id
            )
            return Response(data=auth)

        return Response(status=status.HTTP_403_FORBIDDEN)
    
    def pusher_authorize_user(self, channel_name, socket_id, user):
        user_id = int(channel_name.removeprefix('private-user-'))

        try:
            _ = get_user_model().objects.get(id = user_id)
        except get_user_model().DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if user_id != user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        auth = pusher_client.authenticate(
            channel = channel_name,
            socket_id = socket_id
        )
        return Response(data=auth)


    def trigger_user_channel(self, user_id, projectReadSerializerData, messageReadSerializerData):
        user_channel_name = f'private-user-{user_id}'
            
        pusher_client.trigger(user_channel_name, 'message_sent', {
            'project': projectReadSerializerData,
            'message': messageReadSerializerData
        })

    @action(detail=True, methods=['post'], url_path='agora/rtc-token', permission_classes=[IsAuthenticated, IsMember | IsOwner])
    def agora_rtc_token(self, request, pk=None):
        project = self.get_object()
        uid = request.user.id
        channel_name = f"channel-{project.id}"

        token_expiration_in_seconds = 3600
        privilege_expiration_in_seconds = 3600

        token = RtcTokenBuilder.build_token_with_uid(AGORA_APP_ID, AGORA_APP_CERTIFICATE, channel_name, uid, Role_Publisher, token_expiration_in_seconds, privilege_expiration_in_seconds)

        

        '''
        beams_client.publish_to_users(
            user_ids=user_ids,
            publish_body={
                'web': {
                    'notification': {
                        'title': project.title,
                        'body': 'video call has started',
                        'icon': project.image.url,
                        "deep_link": f'http://localhost:4200/project/{project.id}'
                    }
                }        
            }
        )
        '''

        return Response(data={"agora_token":token})
    

class BeamsAuthView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self, request):
        user = request.user
        print(request.query_params.get('user_id'))
        user_id = request.query_params.get('user_id')
        if user_id != f"user-{user.id}":
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        beams_token = beams_client.generate_token(user_id)

        return Response(data=beams_token)

        


class UserProjectview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id=None):

        if id:
            try:
                user = get_user_model().objects.get(id = id)
            except get_user_model().DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            user = request.user
        
        projectAdminsSerializer = ProjectReadSerializer(user.admin_project_set, many=True)
        projectMembersSerializer = ProjectReadSerializer(user.member_project_set.filter(project_membership_set__status = 2), many=True)
        return Response(data = {'admin_of': projectAdminsSerializer.data, 'member_of': projectMembersSerializer.data})

class TagListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TagSerializer

    def get_queryset(self):
        queryset = Tag.objects.all()
        name = self.request.query_params.get('name')
        if name is not None:
            if name != '':
                return queryset.filter(name__startswith=name).annotate(count = Count("project")).order_by("-count", "name")
        return []
    
class ProjectSerachListView(ListAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=ProjectSearchSerializer

    def get_queryset(self):
        queryset = Project.objects.all()
        search_for = self.request.query_params.get('search_for')

        if search_for is not None:
            search_vectors = (
                SearchVector('title') + 
                SearchVector('description') + 
                SearchVector('admin__first_name') + 
                SearchVector('admin__middle_name') + 
                SearchVector('admin__last_name')
            )

            
            search_query = SearchQuery(search_for)

            queryset = queryset.annotate(
                rank = SearchRank(search_vectors, search_query)
            ).order_by('-rank')

            queryset = queryset.exclude(privacy=2)
            return queryset.distinct()


        return []