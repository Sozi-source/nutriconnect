# NutriApp/filters.py
import django_filters
from .models import Practitioner

class PractitionerFilter(django_filters.FilterSet):
    # Exact matches
    specialties__name = django_filters.CharFilter(field_name='specialties__name', lookup_expr='icontains')
    city = django_filters.CharFilter(lookup_expr='icontains')
    currency = django_filters.CharFilter(lookup_expr='exact')
    years_of_experience = django_filters.NumberFilter()
    is_verified = django_filters.BooleanFilter()
    
    # Range filters for hourly_rate
    hourly_rate_min = django_filters.NumberFilter(field_name='hourly_rate', lookup_expr='gte')
    hourly_rate_max = django_filters.NumberFilter(field_name='hourly_rate', lookup_expr='lte')
    hourly_rate = django_filters.RangeFilter(field_name='hourly_rate')  # For ?hourly_rate=50,100

    class Meta:
        model = Practitioner
        fields = ['specialties__name', 'city', 'currency', 'years_of_experience', 'is_verified']