# Claude-Style Chat Interface Implementation

This document provides details on the Claude-style chat interface implementation for the User Authentication System.

## Overview

The Claude-style interface implements a clean, professional chat UI similar to Anthropic's Claude with the following features:

- Toggle-able sidebar with profile options
- Dark/light mode support
- Professional and minimalist design
- Responsive layout

## Testing the Interface

### Without Backend (UI Testing Only)

To test the interface without requiring the backend API:

1. Open `src/main.jsx` and change `TEST_MODE` to `true`:
   ```jsx
   const TEST_MODE = true;
   ```

2. Start the development server:
   ```
   npm run dev
   ```

3. Access the interface at http://localhost:5173/

This will use the `MockAuthContext` to provide simulated authentication data.

### With Backend Integration

1. Make sure `TEST_MODE` is set to `false` in `src/main.jsx`
2. Ensure the backend API is running
3. Start the frontend development server:
   ```
   npm run dev
   ```
4. Access the interface at http://localhost:5173/chat

## Component Structure

The Claude-style interface is composed of the following key components:

- **ClaudeLayout**: Main layout component that includes the sidebar and content area
- **ClaudeSidebar**: Toggleable sidebar with navigation and profile options
- **ClaudeChatPage**: The main chat page component
- **ThemeContext**: Context provider for dark/light mode functionality

## Features

### Sidebar Toggle

Click the menu icon in the top-left corner to toggle the sidebar visibility.

### Theme Switching

Click on your profile in the bottom-left, then select "Dark mode" or "Light mode" to switch themes.

### Profile Options

Access profile options by clicking on your profile in the bottom-left of the sidebar.

### Chat Interface

The chat interface follows Claude's minimalist design:
- Clean message bubbles
- Distinctive user/assistant styling
- Professional typography and spacing
- Input box with send button at the bottom

## Troubleshooting

### Auth API Issues

If you encounter 404 errors for `/api/auth/me`, ensure:
1. The backend server is running
2. The endpoint is correctly defined in the API
3. The path in `AuthContext.jsx` matches the actual API endpoint

### Path Errors

If you see import errors, check the relative paths in the component imports.