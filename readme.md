# Micro Real Estate Management System (MicroREMS)

MicroREMS is a lightweight, Django-based web application designed for small-scale real estate management. It allows landlords to list and manage properties, and tenants to browse properties, submit rental requests, and manage their tenancy.

## Features

*   **User Roles:**
    *   **Landlord:** Manages properties, rental agreements, payments, and notices.
    *   **Tenant:** Browses properties, requests rentals, manages payments, and views notices.
    *   **General User:** Can browse properties and register as either a landlord or tenant.
*   **Property Management:**
    *   Create, list, update, and delete properties.
    *   Upload and manage multiple property images.
    *   Detailed property views with image carousels, amenities, and descriptions.
*   **Rental Management:**
    *   Tenants can request to rent properties.
    *   Landlords can approve or reject rental requests.
    *   Create and manage digital rental agreements.
    *   Terminate rental agreements.
*   **Payment Tracking:**
    *   Landlords can record rent payments.
    *   Tenants can view their payment history.
    *   Payment status tracking (Pending, Paid, Overdue).
*   **Notice System:**
    *   Landlords and tenants can exchange notices (e.g., maintenance requests, announcements).
    *   Notice status tracking (Sent, Viewed, Resolved).
*   **User Authentication & Profiles:**
    *   Secure user registration and login.
    *   Password reset and change functionality.
    *   User profile management with role-specific details.
*   **Dashboards:**
    *   Tailored dashboards for landlords (property overview, recent activity) and tenants (rental details, upcoming payments).
*   **Admin Interface:**
    *   Comprehensive Django admin interface for site administrators to manage all data.

## Project Structure

```
.microreal_estate/
├── accounts/               # User management, profiles, authentication
├── media/                  # User-uploaded files (profile pics, property images, documents)
├── microreal_estate/       # Core project settings, main URLs
├── payments/               # Payment and notice management
├── properties/             # Property listings, rental agreements, requests
├── static/                 # Static files (CSS, JS, images)
│   ├── css/
│   ├── images/
│   └── js/
├── templates/              # HTML templates organized by app
│   ├── accounts/
│   ├── payments/
│   ├── properties/
│   ├── base.html           # Base layout template
│   └── home.html           # Homepage template
├── manage.py               # Django's command-line utility
└── readme.md               # This file
```

## Tech Stack

*   **Backend:** Django, Python
*   **Frontend:** HTML, Tailwind CSS, (minimal) JavaScript
*   **Database:** SQLite (default, configurable)
*   **Forms:** `django-crispy-forms` with `crispy-bootstrap5` for styling.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd microreal_estate
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(A `requirements.txt` file will need to be generated for this project)*

4.  **Apply migrations:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

5.  **Create a superuser (for admin access):**
    ```bash
    python manage.py createsuperuser
    ```

6.  **Run the development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be accessible at `http://120.0.0.1:8000/`.
    The admin panel will be at `http://120.0.0.1:8000/admin/`.

## Key Configuration Points (`settings.py`)

*   `INSTALLED_APPS`: Includes `accounts`, `properties`, `payments`, `crispy_forms`, `crispy_bootstrap5`.
*   `AUTH_USER_MODEL = 'accounts.User'`: Custom user model.
*   `CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"`
*   `CRISPY_TEMPLATE_PACK = "bootstrap5"`
*   `LOGIN_URL = 'login'`
*   `LOGIN_REDIRECT_URL = 'dashboard'`
*   `LOGOUT_REDIRECT_URL = 'home'`
*   `STATIC_URL`, `STATICFILES_DIRS`, `MEDIA_URL`, `MEDIA_ROOT` are configured for static and media files.

## Further Development / To-Do

*   Generate `requirements.txt`.
*   Implement email notifications for key events (e.g., new rental request, payment due).
*   Add more robust search and filtering for properties.
*   Develop unit and integration tests.
*   Enhance UI/UX with more interactive elements.
*   Implement document uploads for rental agreements.
*   Consider internationalization and localization.
*   Deployment configurations (e.g., Docker, Gunicorn, Nginx).

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

---

This README provides a basic overview. Detailed documentation for each app and module can be found within their respective directories or will be added as the project evolves.

