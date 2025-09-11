# SMTP Configuration Guide

This guide will help you set up SMTP email functionality for your User Authentication System.

## Quick Setup Options

### Option 1: Gmail (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a password for "Mail"
3. **Update your .env file**:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-character-app-password
   SMTP_USE_TLS=true
   SMTP_USE_SSL=false
   FROM_EMAIL=your-email@gmail.com
   FROM_NAME=User Authentication System
   ```

### Option 2: Outlook/Hotmail

```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
FROM_EMAIL=your-email@outlook.com
FROM_NAME=User Authentication System
```

### Option 3: SendGrid (Recommended for Production)

1. **Sign up for SendGrid** (free tier available)
2. **Create an API Key**
3. **Update your .env file**:
   ```bash
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   SMTP_USE_TLS=true
   SMTP_USE_SSL=false
   FROM_EMAIL=your-verified-sender@yourdomain.com
   FROM_NAME=User Authentication System
   ```

### Option 4: Mailgun

```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=your-mailgun-smtp-username
SMTP_PASSWORD=your-mailgun-smtp-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
FROM_EMAIL=your-verified-sender@yourdomain.com
FROM_NAME=User Authentication System
```

## Step-by-Step Setup

### 1. Choose Your Email Provider

For **development**: Gmail (easiest to set up)
For **production**: SendGrid or Mailgun (more reliable, better deliverability)

### 2. Get Your Credentials

#### For Gmail:
- Email: your-email@gmail.com
- Password: Your 16-character app password (NOT your regular password)

#### For SendGrid:
- Username: "apikey" (literally the word "apikey")
- Password: Your SendGrid API key

#### For Mailgun:
- Username: Your Mailgun SMTP username
- Password: Your Mailgun SMTP password

### 3. Update .env File

Edit `backend/.env` and add your SMTP settings:

```bash
# SMTP Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_USE_SSL=false
FROM_EMAIL=your-email@gmail.com
FROM_NAME=User Authentication System
EMAIL_TEMPLATES_DIR=app/templates/email
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24
EMAIL_RESET_TOKEN_EXPIRE_HOURS=2
```

### 4. Test Your Configuration

Run the test script:

```bash
cd tests
python test_smtp.py
```

This will:
- Check your configuration
- Test SMTP connection
- Send test emails
- Verify template rendering

### 5. Restart Your Application

After updating the .env file, restart your backend server:

```bash
cd backend
python main.py
```

## Email Templates Available

Your system includes these pre-built email templates:

1. **Welcome Email** (`welcome.html`) - Sent after registration with verification link
2. **Email Verification** (`email_verification.html`) - For email verification
3. **Password Reset** (`password_reset.html`) - For password reset requests
4. **Security Alert** (`security_alert.html`) - For security notifications

## Testing Email Functionality

### 1. Test SMTP Connection
```bash
cd tests
python test_smtp.py
```

### 2. Test Registration Flow
1. Register a new user through your frontend
2. Check that verification email is sent
3. Click verification link to confirm it works

### 3. Test Password Reset
1. Use the "Forgot Password" feature
2. Check that reset email is sent
3. Use the reset link to change password

## Troubleshooting

### Common Issues:

#### 1. "Authentication failed"
- **Gmail**: Make sure you're using an App Password, not your regular password
- **Other providers**: Verify username/password are correct

#### 2. "Connection refused"
- Check SMTP_HOST and SMTP_PORT settings
- Verify your firewall allows outbound SMTP connections

#### 3. "TLS/SSL errors"
- Try switching SMTP_USE_TLS and SMTP_USE_SSL settings
- For Gmail: TLS=true, SSL=false

#### 4. "Sender not authorized"
- Make sure FROM_EMAIL matches your authenticated email
- For production: verify sender domain with your provider

### Debug Mode:

Enable debug logging by setting in your .env:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

This will show detailed SMTP communication in your logs.

## Production Considerations

### 1. Use Professional Email Service
- SendGrid, Mailgun, Amazon SES
- Better deliverability and reputation
- Detailed analytics and bounce handling

### 2. Email Reputation
- Use a custom domain for FROM_EMAIL
- Set up SPF, DKIM, and DMARC records
- Monitor bounce rates and spam complaints

### 3. Rate Limiting
- Most providers have sending limits
- Implement email queuing for high volume
- Monitor your sending quotas

### 4. Security
- Never commit SMTP credentials to version control
- Use environment variables or secure secrets management
- Rotate credentials regularly

## Need Help?

1. **Run the test script**: `cd tests && python test_smtp.py`
2. **Check the logs**: Look for email-related errors in your application logs
3. **Verify settings**: Double-check all SMTP configuration values
4. **Test manually**: Try sending an email using your credentials with a simple email client

## Email Types in Your System

Your authentication system will automatically send these emails:

- ✅ **Registration Welcome** - When user registers
- ✅ **Email Verification** - To verify email address  
- ✅ **Password Reset** - When user requests password reset
- ✅ **Security Alerts** - For suspicious login attempts
- ✅ **Login Notifications** - For successful logins (optional)

All emails are sent automatically by the system when the appropriate events occur.
