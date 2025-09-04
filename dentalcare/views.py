from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment, CustomUser, ContactSubmission
from .forms import CustomUserSignUpForm, LoginForm, AppointmentForm, ContactForm
import datetime
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import UserProfileForm

def home(request):
    if request.user.is_authenticated and hasattr(request.user, "role") and request.user.role == "doctor":
        return render(request, "doctor_index.html")
    else:
        return render(request, "index.html")

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'profile_edit.html', {'form': form, 'user': user})

def sign_up(request):
    if request.method == "POST":
        form = CustomUserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'patient'
            user.is_staff = False
            user.first_name = form.cleaned_data.get("first_name")
            user.last_name = form.cleaned_data.get("last_name")
            user.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect("home")
    else:
        form = CustomUserSignUpForm()
    return render(request, "sign_up.html", {"form": form})


def login_page(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

def log_out(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("/")

@login_required
def book_appointment(request):
    available_slots = []
    selected_date = None
    selected_doctor = None
    form = AppointmentForm()
    
    if request.method == 'POST':
        # Check Availability
        if 'check_availability' in request.POST:
            doctor_id = request.POST.get('doctor')
            date_str = request.POST.get('date')
            
            if doctor_id and date_str:
                try:
                    selected_doctor = CustomUser.objects.get(id=doctor_id, role='doctor')
                    selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # Check if date is not in the past
                    if selected_date < datetime.date.today():
                        messages.error(request, "Cannot book appointments for past dates.")
                    else:
                        # Get booked slots for this doctor on this date
                        appointments = Appointment.objects.filter(
                            doctor=selected_doctor,
                            date=selected_date
                        ).exclude(status='cancelled')
                        
                        booked_slots = [a.time_slot.strftime("%H:%M:%S") for a in appointments]
                        
                        # Get all time slots and filter available ones
                        all_slots = [(datetime.time(hour, 0), f"{hour:02d}:00") for hour in range(9, 18)]
                        available_slots = [
                            (slot.strftime("%H:%M:%S"), label) 
                            for slot, label in all_slots 
                            if slot.strftime("%H:%M:%S") not in booked_slots
                        ]
                        
                        if not available_slots:
                            messages.warning(request, "No available slots for this doctor on the selected date.")
                        
                        # Preserve form data
                        form = AppointmentForm(initial={
                            'doctor': selected_doctor,
                            'date': selected_date
                        })
                except CustomUser.DoesNotExist:
                    messages.error(request, "Invalid doctor selected.")
                except ValueError:
                    messages.error(request, "Invalid date format.")
            else:
                messages.error(request, "Please select both a doctor and date.")
                form = AppointmentForm(request.POST)
        
        # Book Appointment
        elif 'book_slot' in request.POST:
            doctor_id = request.POST.get('doctor')
            date_str = request.POST.get('date')
            time_slot_str = request.POST.get('time_slot')
            reason = request.POST.get('reason', '')
            
            if not all([doctor_id, date_str, time_slot_str]):
                messages.error(request, "Please select doctor, date and time slot.")
                return redirect('book_appointment')
            
            try:
                selected_doctor = CustomUser.objects.get(id=doctor_id, role='doctor')
                selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                time_slot = datetime.datetime.strptime(time_slot_str, "%H:%M:%S").time()
                
                # Check if date is not in the past
                if selected_date < datetime.date.today():
                    messages.error(request, "Cannot book appointments for past dates.")
                    return redirect('book_appointment')
                
                # Check if user already has 2 appointments for this date
                user_day_count = Appointment.objects.filter(
                    user=request.user, 
                    date=selected_date
                ).exclude(status='cancelled').count()
                
                if user_day_count >= 2:
                    messages.error(request, "You can only book two appointments per day.")
                    return redirect('my_appointments')
                
                # Check if slot is already booked for this doctor
                if Appointment.objects.filter(
                    doctor=selected_doctor,
                    date=selected_date, 
                    time_slot=time_slot
                ).exclude(status='cancelled').exists():
                    messages.error(request, "This time slot is already booked for this doctor.")
                    return redirect('book_appointment')
                
                # Create appointment
                appointment = Appointment.objects.create(
                    user=request.user,
                    doctor=selected_doctor,
                    date=selected_date,
                    time_slot=time_slot,
                    reason=reason,
                    status='pending'
                )
                messages.success(request, f"Appointment booked successfully with {selected_doctor.get_display_name()}! Awaiting confirmation.")
                return redirect('my_appointments')
                
            except CustomUser.DoesNotExist:
                messages.error(request, "Invalid doctor selected.")
            except (ValueError, AttributeError) as e:
                messages.error(request, f"Invalid data format: {str(e)}")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                
            return redirect('book_appointment')

    return render(request, 'book_appointment.html', {
        'form': form,
        'available_slots': available_slots,
        'selected_date': selected_date,
        'selected_doctor': selected_doctor,
    })


@login_required
def my_appointments(request):
    if hasattr(request.user, 'role'):
        if request.user.role == 'doctor':
            appointments = Appointment.objects.filter(
                doctor=request.user
            ).order_by('-date', '-time_slot')
        else:
            appointments = Appointment.objects.filter(
                user=request.user
            ).order_by('-date', '-time_slot')
    else:
        appointments = Appointment.objects.filter(
            user=request.user
        ).order_by('-date', '-time_slot')

    # Add is_expired flag
    now = timezone.now()
    for appt in appointments:
        appt_datetime = timezone.make_aware(datetime.datetime.combine(appt.date, appt.time_slot))
        appt.is_expired = now >= appt_datetime

    return render(request, 'my_appointments.html', {'appointments': appointments})





@login_required
def doctor_index(request):
    if not request.user.is_authenticated or request.user.role != 'doctor':
        messages.error(request, "Access denied. Doctors only.")
        return redirect('home')
    
    today = datetime.date.today()

    # 1️⃣ Today's Appointments
    todays_appointments = Appointment.objects.filter(
        doctor=request.user,
        date=today
    ).exclude(status='cancelled')
    todays_appointments_count = todays_appointments.count()

    # 2️⃣ Today's Messages (Contacts)
    todays_messages_count = ContactSubmission.objects.filter(
        submitted_at__date=today
    ).count()

    # 3️⃣ Total unique patients
    all_appointments = Appointment.objects.filter(doctor=request.user)
    unique_patients_count = all_appointments.values('user').distinct().count()

    context = {
        'todays_appointments_count': todays_appointments_count,
        'todays_messages_count': todays_messages_count,
        'unique_patients_count': unique_patients_count,
        'todays_appointments': todays_appointments,  # optional, if you want to list them
    }

    return render(request, "doctor_index.html", context)



@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    # Only allow the patient who booked, or the doctor, to cancel
    is_patient = appointment.user == request.user
    is_doctor = appointment.doctor == request.user
    # Only allow cancellation before the appointment time
    appointment_datetime = timezone.make_aware(
        datetime.datetime.combine(appointment.date, appointment.time_slot)
    )
    if timezone.now() >= appointment_datetime:
        messages.error(request, "You cannot cancel past or ongoing appointments.")
        # Redirect to the correct page
        if is_patient:
            return redirect('my_appointments')
        else:
            return redirect('total_appointments')
    # Only allow if patient or doctor
    if is_patient or is_doctor:
        if appointment.status in ['pending', 'confirmed']:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, "Appointment cancelled successfully.")
        else:
            messages.warning(request, "This appointment is already cancelled.")
    else:
        messages.error(request, "You do not have permission to cancel this appointment.")
    # Redirect to the correct page
    if is_patient:
        return redirect('my_appointments')
    else:
        return redirect('total_appointments')


@require_POST
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if appointment.status == 'pending':
        appointment.status = 'confirmed'
        appointment.save()
        messages.success(request, "Appointment confirmed.")
    else:
        messages.warning(request, "Only pending appointments can be confirmed.")
    return redirect('total_appointments')



@login_required
def total_appointments(request):
    date = request.GET.get('date')
    if date:
        appointments = Appointment.objects.filter(date=date)
    else:
        appointments = Appointment.objects.all()

    # Add is_expired flag
    now = timezone.now()
    for appt in appointments:
        appt_datetime = timezone.make_aware(datetime.datetime.combine(appt.date, appt.time_slot))
        appt.is_expired = now >= appt_datetime

    return render(request, 'total_appointment.html', {
        'appointments': appointments,
        'selected_date': date
    })



def contact_page(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            if request.user.is_authenticated:
                contact.user = request.user
            contact.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact_page')
    else:
        form = ContactForm()
    return render(request, "contact_page.html", {"form": form})

def is_doctor(user):
    return user.is_authenticated and getattr(user, "role", None) == "doctor"

@login_required
def received_contacts(request):
    if not hasattr(request.user, "role") or request.user.role != "doctor":
        messages.error(request, "Access denied. Doctors only.")
        return redirect("home")
    date = request.GET.get('date')
    contacts = ContactSubmission.objects.all().order_by('-submitted_at')
    if date:
        contacts = contacts.filter(submitted_at__date=date)
    return render(request, "received_contacts.html", {"contacts": contacts, "selected_date": date})

@login_required
def view_contact(request, contact_id):
    if not hasattr(request.user, "role") or request.user.role != "doctor":
        messages.error(request, "Access denied. Doctors only.")
        return redirect("home")
    contact = get_object_or_404(ContactSubmission, id=contact_id)
    return render(request, "view_contact.html", {"contact": contact})

@login_required
@require_POST
def delete_contact(request, contact_id):
    if not hasattr(request.user, "role") or request.user.role != "doctor":
        messages.error(request, "Access denied. Doctors only.")
        return redirect("home")
    contact = get_object_or_404(ContactSubmission, id=contact_id)
    contact.delete()
    messages.success(request, "Contact deleted successfully.")
    return redirect("received_contacts")

@login_required
def doctor_patients(request):
    if not hasattr(request.user, "role") or request.user.role != "doctor":
        messages.error(request, "Access denied. Doctors only.")
        return redirect("home")
    # Get all appointments for this doctor
    appointments = Appointment.objects.filter(doctor=request.user).select_related('user')
    # Collect unique patients
    patients = {}
    for appt in appointments:
        user = appt.user
        if user and user.id not in patients:
            patients[user.id] = user
    return render(request, "doctor_patients.html", {"patients": patients.values()})





@login_required
def profile_view(request):
    user = request.user
    if user.role == "doctor":
        return render(request, "doctor_profile.html", {"user": user})
    else:
        return render(request, "patient_profile.html", {"user": user})