from rest_framework import permissions

class IsClientUser(permissions.BasePermission):
    """
    Custom permission to only allow client users to access.
    Clients have profile.role = 'client'
    """
    
    def has_permission(self, request, view):
        # Allow admins to access everything
        if request.user.is_staff:
            return True
            
        # Check if user is authenticated and has a profile with client role
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'client'
        except:
            return False

class IsPractitionerUser(permissions.BasePermission):
    """
    Custom permission to only allow practitioner users to access.
    Practitioners have profile.role = 'practitioner'
    """
    
    def has_permission(self, request, view):
        # Allow admins to access everything
        if request.user.is_staff:
            return True
            
        # Check if user is authenticated and has a profile with practitioner role
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'practitioner'
        except:
            return False

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_staff:
            return True
            
        # Check if the object has a user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # Check if the object has a client attribute (for consultations)
        if hasattr(obj, 'client'):
            return obj.client == request.user
            
        return False

class IsClientOrAdmin(permissions.BasePermission):
    """
    Allow access only to clients and admins.
    Practitioners cannot access.
    """
    
    def has_permission(self, request, view):
        # Admin can access
        if request.user.is_staff:
            return True
            
        # Check if user is authenticated and is a client
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'client'
        except:
            return False

class IsPractitionerOrAdmin(permissions.BasePermission):
    """
    Allow access only to practitioners and admins.
    Clients cannot access.
    """
    
    def has_permission(self, request, view):
        # Admin can access
        if request.user.is_staff:
            return True
            
        # Check if user is authenticated and is a practitioner
        if not request.user.is_authenticated:
            return False
            
        try:
            return request.user.profile.role == 'practitioner'
        except:
            return False

class CanManageOwnAvailability(permissions.BasePermission):
    """
    Allow practitioners to manage only their own availability.
    Admins can manage all.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_staff:
            return True
            
        # Check if the availability belongs to the practitioner
        return obj.practitioner.user == request.user

class CanManageOwnConsultations(permissions.BasePermission):
    """
    Allow users to manage only their own consultations.
    Clients can view their own, practitioners can view their own.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_staff:
            return True
            
        # Check if user is the client
        if obj.client == request.user:
            return True
            
        # Check if user is the practitioner
        if obj.practitioner.user == request.user:
            return True
            
        return False

class PreventSelfBooking(permissions.BasePermission):
    """
    Prevent practitioners from booking themselves.
    """
    
    def has_permission(self, request, view):
        # Admin can do anything
        if request.user.is_staff:
            return True
            
        # For create operations, check the practitioner being booked
        if request.method == 'POST' and hasattr(request, 'data'):
            practitioner_id = request.data.get('practitioner')
            if practitioner_id:
                try:
                    from .models import Practitioner
                    practitioner = Practitioner.objects.get(id=practitioner_id)
                    # Prevent practitioner from booking themselves
                    if practitioner.user == request.user:
                        return False
                except:
                    pass
                    
        return True