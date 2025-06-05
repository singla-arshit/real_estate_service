from django.urls import path
from . import views

urlpatterns = [
    # Property listing and detail views
    path('', views.property_list, name='property_list'),
    path('<int:property_id>/', views.property_detail, name='property_detail'),
    
    # Landlord property management
    path('create/', views.create_property, name='create_property'),
    path('<int:property_id>/edit/', views.edit_property, name='edit_property'),
    path('<int:property_id>/delete/', views.delete_property, name='delete_property'),
    path('<int:property_id>/images/add/', views.add_property_images, name='add_property_images'),
    path('images/<int:image_id>/delete/', views.delete_property_image, name='delete_property_image'),
    path('images/<int:image_id>/set-primary/', views.set_primary_image, name='set_primary_image'),
    
    # Rental agreements
    path('<int:property_id>/agreements/', views.property_agreements, name='property_agreements'),
    path('agreements/<int:agreement_id>/', views.agreement_detail, name='agreement_detail'),
    path('agreements/<int:agreement_id>/edit/', views.edit_agreement, name='edit_agreement'),
    path('agreements/<int:agreement_id>/terminate/', views.terminate_agreement, name='terminate_agreement'),
    
    # Property requests
    path('<int:property_id>/request/', views.request_property, name='request_property'),
    path('requests/', views.property_requests, name='property_requests'),
    path('requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
]