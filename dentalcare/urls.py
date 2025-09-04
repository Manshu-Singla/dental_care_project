from django.urls import path
 
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('log_in/', views.login_page, name='log_in'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('log_out/', views.log_out, name='log_out'),
    path('doctor_index/', views.doctor_index, name='doctor_index'),
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('my_appointments/', views.my_appointments, name='my_appointments'),
    
    path('appointments/', views.total_appointments, name='total_appointments'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),



    path('contact_us/', views.contact_page, name='contact_page'),
    path('received_contacts/', views.received_contacts, name='received_contacts'),
    path('contact/<int:contact_id>/', views.view_contact, name='view_contact'),
    path('contact/<int:contact_id>/delete/', views.delete_contact, name='delete_contact'),
    path('doctor_patients/', views.doctor_patients, name='doctor_patients'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
