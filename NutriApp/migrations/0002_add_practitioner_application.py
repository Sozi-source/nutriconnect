from django.db import migrations, models
import django.db.models.deletion
import django.core.validators

class Migration(migrations.Migration):
    dependencies = [
        ('NutriApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PractitionerApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bio', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('hourly_rate', models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('years_of_experience', models.PositiveIntegerField()),
                ('qualifications', models.TextField(help_text='Degrees, certifications, etc.')),
                ('license_number', models.CharField(max_length=100)),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('more_info', 'More Info Needed')], default='pending', max_length=20)),
                ('admin_notes', models.TextField(blank=True, help_text='Internal admin notes')),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_applications', to='NutriApp.user')),
                ('specialties', models.ManyToManyField(blank=True, to='NutriApp.specialty')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='practitioner_application', to='NutriApp.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
