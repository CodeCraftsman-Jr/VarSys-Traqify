# 🚀 Traqify Setup Guide

Welcome to Traqify! This guide will help you set up your own instance of the Personal Finance Dashboard with your own credentials and configuration.

## 📋 Prerequisites

- Python 3.8 or higher
- Firebase project (for data storage and authentication)
- Google Cloud project (for Google Tasks integration - optional)

## 🔧 Quick Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/traqify.git
cd traqify
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your credentials (see detailed instructions below).

### 3. Run the Application

```bash
python main.py
```

## 🔐 Detailed Configuration

### Firebase Setup (Required)

1. **Create Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Click "Create a project"
   - Follow the setup wizard

2. **Get Firebase Web Configuration**
   - In Firebase Console, go to Project Settings > General
   - Scroll down to "Your apps" section
   - Click "Web" icon to add a web app
   - Copy the configuration values

3. **Enable Authentication**
   - Go to Authentication > Sign-in method
   - Enable "Email/Password" provider

4. **Setup Realtime Database**
   - Go to Realtime Database
   - Create database in test mode
   - Note the database URL

5. **Get Service Account Key (Optional - for advanced features)**
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Download the JSON file
   - Minify the JSON (remove line breaks) for the environment variable

### Google Tasks Integration Setup (Optional)

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Google Tasks API**
   - Go to APIs & Services > Library
   - Search for "Google Tasks API"
   - Click "Enable"

3. **Create OAuth Credentials**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the credentials JSON

## 📝 Environment Variables

Edit your `.env` file with the following values:

### Firebase Configuration
```env
FIREBASE_API_KEY=your_firebase_api_key_here
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_AUTH_DOMAIN=your-firebase-project-id.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-firebase-project-id-default-rtdb.region.firebasedatabase.app
FIREBASE_STORAGE_BUCKET=your-firebase-project-id.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
FIREBASE_APP_ID=your_firebase_app_id

# Optional: Firebase Service Account (minified JSON)
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"..."}
```

### Google OAuth Configuration (Optional)
```env
GOOGLE_OAUTH_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_OAUTH_PROJECT_ID=your-google-cloud-project-id
```

### Application Settings
```env
DEBUG=false
LOG_LEVEL=INFO
BACKEND_TYPE=direct_firebase
REMEMBER_SESSION=true
```

## 🔍 Verification

After setup, verify your configuration:

1. **Check Firebase Connection**
   - Run the application
   - Try creating an account
   - Check if data syncs to Firebase

2. **Check Google Tasks (if configured)**
   - Go to Todos module
   - Try syncing with Google Tasks
   - Verify tasks appear in both places

## 🚨 Security Best Practices

1. **Never commit credentials to version control**
   - The `.env` file is already in `.gitignore`
   - Always use environment variables in production

2. **Use Firebase Security Rules**
   - Configure proper read/write rules in Firebase
   - Restrict access to authenticated users only

3. **Rotate credentials regularly**
   - Generate new API keys periodically
   - Update OAuth credentials as needed

4. **Use HTTPS in production**
   - Configure SSL certificates
   - Use secure hosting platforms

## 🐛 Troubleshooting

### Common Issues

1. **"Firebase not configured" error**
   - Check your `.env` file exists and has correct values
   - Verify Firebase project settings match your configuration

2. **"Google Tasks integration disabled" warning**
   - This is normal if you haven't configured Google OAuth
   - Google Tasks integration is optional

3. **Authentication errors**
   - Verify Firebase Authentication is enabled
   - Check if Email/Password provider is active

4. **Database connection errors**
   - Verify Firebase Realtime Database URL is correct
   - Check database rules allow authenticated access

### Getting Help

- Check the logs in the `logs/` directory
- Enable debug mode: `DEBUG=true` in `.env`
- Review Firebase Console for error messages
- Check network connectivity and firewall settings

## 📚 Additional Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Google Tasks API Documentation](https://developers.google.com/tasks)
- [Python Environment Variables Guide](https://docs.python.org/3/library/os.html#os.environ)

## 🤝 Contributing

If you encounter issues with this setup guide or have suggestions for improvement, please open an issue or submit a pull request.

---

**⚠️ Important**: This application handles personal financial data. Always ensure your Firebase project has proper security rules and your credentials are kept secure.
