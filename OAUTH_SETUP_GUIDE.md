# Google OAuth 2.0 Setup Guide

## Step 1: Google Cloud Console Setup

### 1.1 Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `User Authentication System`
4. Click "Create"

### 1.2 Enable Google+ API
1. In the left sidebar, go to "APIs & Services" → "Library"
2. Search for "Google+ API" 
3. Click on it and click "Enable"
4. Also enable "Google Identity Services API"

### 1.3 Configure OAuth Consent Screen
1. Go to "APIs & Services" → "OAuth consent screen"
2. Choose "External" (for testing) or "Internal" (if you have a Google Workspace)
3. Fill in required fields:
   - **App name**: `User Authentication System`
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click "Save and Continue"
5. **Scopes**: Click "Add or Remove Scopes"
   - Add: `userinfo.email`
   - Add: `userinfo.profile` 
   - Add: `openid`
6. Click "Save and Continue"
7. **Test users** (for External apps): Add your email for testing
8. Click "Save and Continue"

### 1.4 Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Set name: `Auth System Web Client`
5. **Authorized redirect URIs**: Add these URLs:
   ```
   http://localhost:8000/api/v1/auth/oauth/google/callback
   http://localhost:3000/auth/callback
   ```
6. Click "Create"
7. **Copy the Client ID and Client Secret** - you'll need these!

## Step 2: Environment Configuration

### 2.1 Backend Environment Variables
1. In your backend directory, create/update `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/auth_system

# JWT Configuration  
SECRET_KEY=your-super-secret-jwt-key-here-make-it-long-and-random
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/oauth/google/callback

# Email Configuration (if using SendGrid)
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Your App Name

# Application Settings
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=development
DEBUG=true
```

### 2.2 Frontend Environment Variables
1. In your frontend directory, create/update `.env` file:
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=User Authentication System
```

## Step 3: Testing OAuth Flow

### 3.1 Test OAuth Endpoints
1. Visit: `http://localhost:8000/api/v1/auth/oauth/providers`
2. You should see Google listed as an available provider

### 3.2 Test Frontend Integration
1. Visit: `http://localhost:3000/login`
2. You should see "Continue with Google" button
3. Click it to test the OAuth flow

## Step 4: Troubleshooting

### Common Issues:

**Error: "redirect_uri_mismatch"**
- Make sure the redirect URI in Google Console exactly matches your backend URL
- Check: `http://localhost:8000/api/v1/auth/oauth/google/callback`

**Error: "invalid_client"**  
- Double-check your Client ID and Client Secret in `.env`
- Ensure no extra spaces or quotes

**Error: "access_blocked"**
- Make sure you added your email to test users in OAuth consent screen
- Check that required scopes are added

**Frontend not connecting to backend**
- Verify VITE_API_URL is set correctly
- Check that both servers are running

## Step 5: Production Considerations

### Security:
- Use strong, unique SECRET_KEY in production
- Set ENVIRONMENT=production
- Use HTTPS URLs for redirect URIs
- Store sensitive keys in secure environment variables

### Google Console:
- Submit app for verification if needed
- Add production domains to authorized origins
- Set up proper privacy policy and terms of service

## Testing Checklist:
- [ ] Google Cloud project created
- [ ] OAuth consent screen configured  
- [ ] OAuth credentials created
- [ ] Backend .env configured with Google credentials
- [ ] Frontend .env configured
- [ ] Both servers running
- [ ] OAuth providers endpoint returns Google
- [ ] Login page shows Google button
- [ ] OAuth flow completes successfully
- [ ] User can sign in and access dashboard
