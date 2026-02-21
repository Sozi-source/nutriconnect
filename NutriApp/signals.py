from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile, Practitioner


@receiver(post_save, sender=UserProfile)
def sync_practitioner_with_role(sender, instance, created, **kwargs):

    if instance.role == 'practitioner':
        if not hasattr(instance.user, 'practitioner'):
            Practitioner.objects.create(
                user=instance.user,
                bio='',
                city='',
                hourly_rate=0.00,
                currency='KES',
                years_of_experience=0,
                is_verified=False,
                profile_complete=False
            )

    elif instance.role == 'client':
        if hasattr(instance.user, 'practitioner'):
            instance.user.practitioner.delete()