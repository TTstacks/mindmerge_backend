from rest_framework import serializers
from projects.models import Project, Tag, Membership, Message
from django.contrib.auth import get_user_model
from users.serializers import UserReadSerializer, StudentSerializer, UserShortSerializer


class TagSerializer(serializers.ModelSerializer):
    usage_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['name', 'usage_count']
        read_only_fields = ['usage_count']

    def get_usage_count(self, obj):
        return obj.project_set.count()

class ProjectSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=False)


    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'tags', 'privacy']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        admin = validated_data.pop('admin')
        tags_data = validated_data.pop('tags')
        project = self.Meta.model(**validated_data)
        project.admin = admin
        project.save()
        print('fuck')
        project.tags.add(*[Tag.objects.get_or_create(name=tag_data.get('name'))[0] for tag_data in tags_data])
        print('damna')
        
        return project
    
    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.privacy = validated_data.get('privacy', instance.privacy)
        instance.save()
        instance.tags.clear()
        instance.tags.add(*[Tag.objects.get_or_create(name=tag_data.name)[0] for tag_data in tags_data])
        return instance
    

class ProjectSearchSerializer(serializers.ModelSerializer):
    admin = UserShortSerializer(many=False, read_only=True)


    class Meta:
        model=Project
        fields=['title', 'description', 'admin']

class ProjectReadSerializer(serializers.ModelSerializer):
    admin = UserReadSerializer()
    tags = TagSerializer(many=True)
    members = serializers.SerializerMethodField()


    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'tags', 'admin', 'members', 'privacy', 'image']

    def get_members(self, obj):
        membership = Membership.objects.filter(project = obj).filter(status=2)
        return membership.count()

class ProjectImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['image']

class MembershipSerializer(serializers.ModelSerializer):
    status = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Membership
        fields = ['status', 'join_request_text']
    
    def create(self, validated_data):
        user = validated_data.pop('user')
        project = validated_data.pop('project')
        join_request_text = validated_data.pop('join_request_text')
        membership = Membership.objects.create(user = user, project = project, join_request_text = join_request_text)
        return membership
    
    def update(self, instance, validated_data):
        status = validated_data['status']

        if status == 1 or instance.status == status:
            raise serializers.ValidationError('too bad not too good')

        instance.status = validated_data['status']
        instance.save()
        return instance

class MembershipReadSerializer(serializers.ModelSerializer):
    user = UserReadSerializer()

    class Meta:
        model = Membership
        fields = ['id', 'status', 'join_request_text', 'user']


class MessageAuthorSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    class Meta:
        model = get_user_model()
        fields = ['id', 'first_name', 'middle_name', 'last_name', 'student']

class MessageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ['text', 'media']

    def create(self, validated_data):
        user = validated_data.pop('user')
        project = validated_data.pop('project')
        media = validated_data.get('media', None)
        message = Message.objects.create(user = user, project = project, text = validated_data['text'])
        return message
    
    def validate(self, attrs):
        if not attrs['text'] and not attrs['media']:
            return serializers.ValidationError('message content is empty')
        return attrs

class MessageSerializerRead(serializers.ModelSerializer):
    user = MessageAuthorSerializer()
    class Meta:
        model = Message
        fields = ['id', 'project', 'user', 'text', 'parent', 'media', 'time']