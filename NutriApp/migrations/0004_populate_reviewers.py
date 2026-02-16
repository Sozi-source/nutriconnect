from django.db import migrations

def assign_reviewers_from_consultations(apps, schema_editor):
    Review = apps.get_model('NutriApp', 'Review')
    for review in Review.objects.all():
        # If the review has a consultation with a client, use that as reviewer
        if review.consultation and review.consultation.client:
            review.reviewer = review.consultation.client
            review.save()
            print(f"Updated review {review.id} to client {review.consultation.client.id}")

def assign_default_reviewer(apps, schema_editor):
    # Fallback function if no consultation/client exists
    Review = apps.get_model('NutriApp', 'Review')
    User = apps.get_model('NutriApp', 'User')
    
    # Get the first user as default (or create one if needed)
    default_user = User.objects.first()
    if default_user:
        for review in Review.objects.filter(reviewer__isnull=True):
            review.reviewer = default_user
            review.save()
            print(f"Assigned default user {default_user.id} to review {review.id}")

class Migration(migrations.Migration):

    dependencies = [
        ('NutriApp', '0003_alter_review_reviewer'),
    ]

    operations = [
        # First try to assign from consultation clients
        migrations.RunPython(assign_reviewers_from_consultations),
        # Then assign default to any remaining null reviewers
        migrations.RunPython(assign_default_reviewer),
    ]