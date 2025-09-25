# Claude UI Implementation

This is an implementation of a Claude-style chat interface for our User Authentication System. The UI is designed to mimic the professional and minimal style of Anthropic's Claude AI assistant.

## Components

### 1. ClaudeLayout.jsx

The main layout component that includes:
- Toggleable sidebar 
- Top navigation bar with menu toggle
- Claude branding
- Free plan indicator with upgrade option
- Content area that adjusts when sidebar toggles

### 2. ClaudeSidebar.jsx

The sidebar component that includes:
- Claude header
- Navigation links (New chat, Chats, Projects, Artifacts)
- Recent conversations section
- User profile section at the bottom
- Profile dropdown menu with options for:
  - Theme toggle (Dark/Light mode)
  - Settings
  - Profile
  - Help
  - Sign out

### 3. ClaudeChatPage.jsx

The main chat interface that includes:
- Welcome header when no messages are present
- Chat message area displaying conversation history
- Message input area with send button
- Loading indicator for AI responses
- Quick suggestion buttons for common tasks

## Features

- **Dark Mode**: Fully implemented dark theme throughout the interface
- **Responsive Layout**: Sidebar can be toggled for more screen space
- **Professional Styling**: Clean, minimal design matching Claude's aesthetic
- **Message History**: Clear visual distinction between user and AI messages
- **Quick Actions**: Suggestion buttons for common tasks

## Usage

Navigate to the `/chat` route to access the Claude-style chat interface. The interface allows users to:
- Start new conversations
- View message history
- Toggle the sidebar
- Access settings and profile options
- Switch between light and dark mode

## Development

This implementation uses:
- React for component structure
- React Router for navigation
- Context API for theme and authentication management
- Tailwind CSS for styling

## Styling Notes

The Claude UI follows these design principles:
- Dark color scheme: Primarily black backgrounds with gray accents
- Minimal UI elements: Clean, distraction-free interface
- Orange accent color for interactive elements
- Clear visual hierarchy with proper spacing and typography