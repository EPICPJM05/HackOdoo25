# Skill Swap Platform

A full-stack web application for exchanging skills and knowledge between users. Built with Flask, SQLAlchemy, and Bootstrap.

## Team Name - Solvers
### Members: 
- Poojan Mehta - poojan.mehta2005@gmail.com
- Namra Parikh - namraparikh710@gmail.com
- Parshv Mehta - parshvmehta7000@gmail.com
- Harshit Dave - harshitbbdave@gmail.com

## 🚀 Features

### User Features
- **User Registration & Authentication**: Secure user registration and login system
- **Profile Management**: Create and edit profiles with skills, availability, and photos
- **Skill Listing**: List skills you offer and want to learn
- **Search & Discovery**: Find users by skills with advanced search functionality
- **Swap Requests**: Send and manage skill swap requests
- **Real-time Notifications**: Get instant updates on swap requests via WebSocket
- **Rating System**: Rate and review swap partners after completed exchanges
- **Availability Management**: Set your availability for skill exchanges

### Admin Features
- **User Management**: View, ban, and manage user accounts
- **Skill Moderation**: Approve or reject skill submissions
- **Swap Monitoring**: Monitor all swap requests and their status
- **Reports**: Generate and download comprehensive reports
- **Dashboard**: Real-time statistics and platform overview

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML, CSS, JavaScript with Bootstrap 5
- **Real-time**: Flask-SocketIO for WebSocket connections
- **Authentication**: Flask-Login with password hashing
- **File Upload**: Secure file handling for profile photos

## 📋 Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd skill_swap_project
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```sql
-- Create the database
CREATE DATABASE skill_swap;
USE skill_swap;

-- The application will automatically create all tables on first run
```

### 5. Environment Configuration
Copy the example environment file and configure it:
```bash
cp env.example .env
```

Edit `.env` with your database credentials:
```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=mysql://username:password@localhost/skill_swap
```

### 6. Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5001`

## 📁 Project Structure

```
skill_swap_project/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py             # User model
│   │   ├── skill.py            # Skill model
│   │   ├── user_skill.py       # User-Skill relationship
│   │   ├── swap_request.py     # Swap request model
│   │   ├── feedback.py         # Feedback model
│   │   ├── availability.py     # Availability model
│   │   └── admin.py           # Admin model
│   ├── routes/                 # Flask blueprints
│   │   ├── main.py            # Main routes
│   │   ├── auth.py            # Authentication routes
│   │   ├── users.py           # User management routes
│   │   ├── swaps.py           # Swap management routes
│   │   ├── feedback.py        # Feedback routes
│   │   └── admin.py           # Admin routes
│   ├── templates/              # Jinja2 templates
│   │   ├── base.html          # Base template
│   │   ├── index.html         # Homepage
│   │   └── ...                # Other templates
│   ├── static/                 # Static files
│   │   ├── css/style.css      # Custom CSS
│   │   ├── js/main.js         # Custom JavaScript
│   │   └── uploads/           # User uploads
│   └── utils/                  # Utility functions
│       └── validators.py      # Form validation
├── migrations/                 # Database migrations
├── requirements.txt            # Python dependencies
├── run.py                     # Application entry point
└── README.md                  # This file
```

## 🔧 Configuration

### Database Configuration
The application uses MySQL. Update the `DATABASE_URL` in your `.env` file:
```
DATABASE_URL=mysql://username:password@localhost/skill_swap
```

### File Upload Configuration
Profile photos are stored in `app/static/uploads/`. Ensure this directory is writable.

### Admin Access
Default admin credentials:
- Email: `admin@skillswap.com`
- Password: `admin123`

**Important**: Change these credentials in production!

## 🚀 Usage

### For Users
1. **Register**: Create an account with your email and password
2. **Complete Profile**: Add your skills, availability, and profile photo
3. **Search**: Find users with skills you want to learn
4. **Send Requests**: Propose skill swaps with other users
5. **Manage Swaps**: Accept, reject, or complete swap requests
6. **Rate Partners**: Provide feedback after completed swaps

### For Admins
1. **Login**: Use admin credentials to access admin panel
2. **Monitor Users**: View and manage user accounts
3. **Moderate Skills**: Approve or reject skill submissions
4. **Generate Reports**: Download comprehensive platform reports
5. **Monitor Activity**: Track swap requests and user activity

## 🔒 Security Features

- **Password Hashing**: All passwords are hashed using bcrypt
- **CSRF Protection**: Built-in CSRF protection for forms
- **Input Validation**: Comprehensive form validation and sanitization
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy
- **File Upload Security**: Secure file handling with validation
- **Session Management**: Secure session handling with Flask-Login

## 📊 Database Schema

### Core Tables
- **users**: User accounts and profiles
- **skills**: Available skills in the platform
- **user_skills**: Many-to-many relationship (offered/wanted skills)
- **swap_requests**: Skill swap requests between users
- **feedback**: Ratings and reviews after swaps
- **availability**: User availability time slots
- **admins**: Admin user accounts

### Key Relationships
- Users can have multiple skills (offered/wanted)
- Swap requests connect two users with specific skills
- Feedback is linked to completed swaps
- Availability slots belong to users

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Production Deployment
1. Set `FLASK_ENV=production` in environment
2. Use a production WSGI server (Gunicorn)
3. Set up a reverse proxy (Nginx)
4. Configure SSL certificates
5. Set up database backups

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added real-time notifications
- **v1.2.0**: Enhanced admin dashboard
- **v1.3.0**: Improved search functionality

## 🎯 Roadmap

- [ ] Email notifications
- [ ] Mobile app
- [ ] Advanced search filters
- [ ] Skill categories
- [ ] Video chat integration
- [ ] Payment integration
- [ ] API for third-party integrations

---

**Built with ❤️ for the hackathon community** 