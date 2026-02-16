from rest_framework.permissions import BasePermission

# The owner can access and modify their own resources. Admin has full control
class IsConsultationClientOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.consultation.client == request.user

class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj == request.user

class IsRelatedUserOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user

class IsAvailabilityOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.practitioner.user == request.user

class IsConsultationParticipantOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return (
            obj.client == request.user or
            obj.practitioner.user == request.user
        )

class IsReviewOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.consultation.client == request.user
  