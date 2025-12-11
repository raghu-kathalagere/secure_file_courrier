# Secure File Courier

A Flask-based web application for secure file sharing and storage with user authentication and encryption support.

## Features

- **User Authentication**: Secure user registration and login with bcrypt password hashing
- **File Management**: Upload, download, and manage files with a responsive dashboard
- **Encryption**: Encrypted file storage using PyCryptodome for enhanced security
- **Session Management**: Secure session handling with Flask-Login
- **Form Validation**: Email validation and CSRF protection with Flask-WTF
- **File Limits**: 100 MB maximum file upload size
- **Database**: SQLite for user and file metadata storage

## Technologies

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt, Flask-WTF
- **Security**: Bcrypt (password hashing), PyCryptodome (file encryption)
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Validation**: Email-validator

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/raghu-kathalagere/secure_file_courrier.git
   cd secure_file_courrier
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (optional)
   ```bash
   # Create a .env file
   echo SECRET_KEY=your-secret-key-here > .env
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

   The application will be available at `http://127.0.0.1:5000`

## Usage

### Getting Started

1. **Register a new account**
   - Navigate to the registration page
   - Enter your email and password
   - Create your account

2. **Login**
   - Use your credentials to login
   - Your session will be remembered for 7 days

3. **Upload Files**
   - Click on "Upload" in the dashboard
   - Select a file (max 100 MB)
   - Files are automatically encrypted and stored securely

4. **Manage Files**
   - View all your uploaded files in the dashboard
   - Download files when needed
   - Delete files you no longer need
   - View file details and activity logs

## Project Structure

```
secure_file_courier/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── crypto_utils.py          # Encryption utilities
│   ├── extensions.py            # Flask extensions (DB, Login, Bcrypt)
│   ├── models.py                # Database models
│   ├── storage_utils.py         # File storage utilities
│   ├── auth/                    # Authentication module
│   │   ├── routes.py            # Auth routes (login, register)
│   │   ├── forms.py             # Login/Register forms
│   │   └── __init__.py
│   ├── files/                   # File management module
│   │   ├── routes.py            # File routes (upload, download)
│   │   ├── forms.py             # File upload forms
│   │   └── __init__.py
│   ├── static/                  # Static files
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/               # HTML templates
│       ├── base.html            # Base template
│       ├── auth/                # Auth templates
│       │   ├── login.html
│       │   └── register.html
│       └── files/               # File templates
│           ├── dashboard.html
│           ├── file_detail.html
│           ├── logs.html
│           └── upload.html
├── data/                        # Uploaded files directory
├── config.py                    # Configuration settings
├── run.py                       # Application entry point
├── requirements.txt             # Project dependencies
└── README.md                    # This file
```

## Configuration

Edit `config.py` to customize settings:

```python
# Secret key for session management
SECRET_KEY = "your-secret-key"

# Maximum file upload size (default: 100 MB)
MAX_CONTENT_LENGTH = 100 * 1024 * 1024

# Database location
SQLALCHEMY_DATABASE_URI = "sqlite:///secure_courier.db"

# Session cookie settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True for HTTPS
```

## Security Considerations

⚠️ **Important**: This application is in development mode. Before deploying to production:

1. Change the `SECRET_KEY` in `config.py` to a strong, random value
2. Set `debug=False` in `run.py`
3. Enable `SESSION_COOKIE_SECURE = True` when using HTTPS
4. Use a production-grade database (PostgreSQL, MySQL)
5. Set up proper HTTPS/SSL certificates
6. Configure environment variables properly with a `.env` file
7. Run behind a production WSGI server (Gunicorn, uWSGI)

## API Endpoints

### Authentication
- `POST /register` - Register a new user
- `POST /login` - Login user
- `GET /logout` - Logout user

### Files
- `GET /dashboard` - View file dashboard
- `GET /upload` - Upload file page
- `POST /upload` - Process file upload
- `GET /file/<file_id>` - View file details
- `GET /download/<file_id>` - Download file
- `DELETE /file/<file_id>` - Delete file
- `GET /logs` - View activity logs

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, modify `run.py`:
```python
app.run(host="127.0.0.1", port=8000, debug=True)
```

### Database Errors
Delete `secure_courier.db` to reset the database:
```bash
rm secure_courier.db  # or del secure_courier.db on Windows
```

### Import Errors
Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Author

**Raghu Kathalagere**

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Note**: This is a development project. Always review security practices before using in production environments.
