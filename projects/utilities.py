from projects.models import Project
from projects.serializers import ProjectReadSerializer


def trigger_member_event(pusher_client, channel_name, event_name, projectReadSerializerData, membershipReadSerializerData):
    pusher_client.trigger(channel_name, event_name, {
        'project': projectReadSerializerData,
        'member': membershipReadSerializerData,
    })

def process_agora_webhook(pusher_client, beams_client, event_type, channel_name, payload):

    if channel_name == 'test_webhook':
        return

    project_id = int(channel_name.removeprefix('channel-'))
    project = Project.objects.get(id = project_id)
    projectReadSerializer = ProjectReadSerializer(project)

    user_ids=[f'user-{project.admin.id}']

    event_name = 'video_started' if event_type == 101 else 'video_ended'



    accepted_members = project.members.filter(user_membership_set__status=2).distinct()
    admin_can_get_notification = True
    body_text = 'video call has started' if event_type == 101 else 'video call has ended'

    if event_type == 102:
        last_uid = payload.get('lastUid')
        accepted_members = accepted_members.exclude(id=last_uid)
        if last_uid == project.admin.id:
            admin_can_get_notification = False
    
    if admin_can_get_notification:
        pusher_client.trigger(f'private-user{project.admin.id}', event_name, {
            'project': projectReadSerializer.data,
            'video_message': body_text
        })

    user_ids.extend([f'user-{member.id}' for member in accepted_members])
    pusher_client.trigger([f'private-user-{member.id}' for member in accepted_members], event_name, {
        'project': projectReadSerializer.data,
        'video_message': body_text
    })

    
    
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