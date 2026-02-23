from rest_framework import permissions

class IsClientUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'client'
        except:
            return False

class IsPractitionerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'practitioner'
        except:
            return False

class IsClientOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'client'
        except:
            return False

class IsPractitionerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
            
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'practitioner'
        except:
            return False

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        if hasattr(obj, 'client'):
            return obj.client == request.user
            
        if hasattr(obj, 'practitioner'):
            return obj.practitioner.user == request.user
            
        return False

class CanManageOwnAvailability(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        return obj.practitioner.user == request.user

class CanManageOwnConsultations(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if obj.client == request.user:
            return True
            
        if obj.practitioner.user == request.user:
            return True
            
        return False

class PreventSelfBooking(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
            
        if request.method == 'POST' and hasattr(request, 'data'):
            practitioner_id = request.data.get('practitioner')
            if practitioner_id:
                try:
                    from .models import Practitioner
                    practitioner = Practitioner.objects.get(id=practitioner_id)
                    if practitioner.user == request.user:
                        return False
                except:
                    pass
                    
        return True

class CanManageOwnApplication(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.user.is_staff:
            return True
            
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        return obj.user == request.user

class CanSubmitApplication(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        from .models import PractitionerApplication
        
        try:
            app = PractitionerApplication.objects.get(user=request.user)
            if app.status not in ['rejected', 'draft']:
                return False
        except PractitionerApplication.DoesNotExist:
            pass
            
        return True

class CanWriteReview(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        if request.method == 'POST':
            consultation_id = request.data.get('consultation')
            if consultation_id:
                try:
                    from .models import Consultation
                    consultation = Consultation.objects.get(id=consultation_id)
                    
                    if consultation.client != request.user:
                        return False
                    
                    if consultation.status != 'completed':
                        return False
                    
                    if hasattr(consultation, 'review'):
                        return False
                        
                except Consultation.DoesNotExist:
                    return False
                    
        return True

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        return request.user.is_staff

class IsOwnerOrPractitionerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
            
        if hasattr(obj, 'client') and obj.client == request.user:
            return True
            
        if hasattr(obj, 'practitioner') and obj.practitioner.user == request.user:
            return True
            
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
            
        return False