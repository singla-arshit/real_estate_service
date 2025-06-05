from django.urls import path
from . import views

urlpatterns = [
    # Payment management
    path('', views.payment_list, name='payment_list'),
    path('<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('create/<int:agreement_id>/', views.create_payment, name='create_payment'),
    path('<int:payment_id>/edit/', views.edit_payment, name='edit_payment'),
    path('<int:payment_id>/mark-completed/', views.mark_payment_completed, name='mark_payment_completed'),
    
    # Tenant payment views
    # path('tenant/', views.tenant_payments, name='tenant_payments'), # This view seems to be payment_list filtered for tenant
    path('tenant/make/<int:payment_id>/', views.tenant_make_payment, name='make_payment'),
    
    # Notice management
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/<int:notice_id>/', views.notice_detail, name='notice_detail'),
    path('notices/create/<int:agreement_id>/', views.create_notice, name='create_notice'),
    path('notices/<int:notice_id>/edit/', views.edit_notice, name='edit_notice'),
    path('notices/<int:notice_id>/mark-resolved/', views.mark_notice_resolved, name='mark_notice_resolved'),
    
    # Tenant notice views (use existing views with filtering)
    # path('notices/tenant/', views.notice_list, name='tenant_notices'), # Covered by notice_list
    path('notices/tenant/create/<int:agreement_id>/', views.create_notice, name='tenant_create_notice'),
]