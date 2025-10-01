from rest_framework import permissions

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.admin == request.user

class IsMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.members.through.objects.filter(status = 2, user = request.user, project = obj).exists()

class IsNotOwnerAndNotMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return not obj.members.through.objects.filter(status = 2, user = request.user, project=obj).exists() and obj.admin != request.user
    
class IsNotOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.admin != request.user