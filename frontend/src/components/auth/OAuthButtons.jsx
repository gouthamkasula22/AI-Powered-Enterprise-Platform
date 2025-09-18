import React from 'react';
import { FcGoogle } from 'react-icons/fc';
import { FaGithub } from 'react-icons/fa';

const GoogleLoginButton = ({ 
    onLoading = () => {}, 
    disabled = false,
    className = "",
    children = "Continue with Google"
}) => {
    const handleGoogleLogin = () => {
        onLoading(true);
        
        // Redirect to backend OAuth endpoint
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        
        // Use the backend callback URL that Google will redirect to
        const redirectUri = `${backendUrl}/api/v1/auth/oauth/google/callback`;
        
        // Store the current page URL to redirect back after auth
        const returnUrl = window.location.pathname;
        if (returnUrl !== '/login' && returnUrl !== '/register') {
            localStorage.setItem('oauth_return_url', returnUrl);
        }
        
        window.location.href = `${backendUrl}/api/v1/auth/oauth/google/login?redirect_uri=${encodeURIComponent(redirectUri)}`;
    };

    return (
        <button
            onClick={handleGoogleLogin}
            disabled={disabled}
            className={`
                w-full flex items-center justify-center gap-3 px-4 py-3
                border border-gray-300 rounded-lg
                bg-white hover:bg-gray-50
                text-gray-700 font-medium
                transition-colors duration-200
                disabled:opacity-50 disabled:cursor-not-allowed
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                ${className}
            `}
        >
            <FcGoogle className="w-5 h-5" />
            <span>{children}</span>
        </button>
    );
};

const GitHubLoginButton = ({ 
    onLoading = () => {}, 
    disabled = false,
    className = "",
    children = "Continue with GitHub"
}) => {
    const handleGitHubLogin = () => {
        onLoading(true);
        
        // Redirect to backend OAuth endpoint
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const currentUrl = window.location.origin;
        const redirectUri = `${currentUrl}/auth/callback`;
        
        // Store the current page URL to redirect back after auth
        const returnUrl = window.location.pathname;
        if (returnUrl !== '/login' && returnUrl !== '/register') {
            localStorage.setItem('oauth_return_url', returnUrl);
        }
        
        window.location.href = `${backendUrl}/api/v1/auth/oauth/github/login?redirect_uri=${encodeURIComponent(redirectUri)}`;
    };

    return (
        <button
            onClick={handleGitHubLogin}
            disabled={disabled}
            className={`
                w-full flex items-center justify-center gap-3 px-4 py-3
                border border-gray-300 rounded-lg
                bg-gray-900 hover:bg-gray-800
                text-white font-medium
                transition-colors duration-200
                disabled:opacity-50 disabled:cursor-not-allowed
                focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2
                ${className}
            `}
        >
            <FaGithub className="w-5 h-5" />
            <span>{children}</span>
        </button>
    );
};

const OAuthButtons = ({ 
    onLoading = () => {}, 
    disabled = false,
    showDivider = true,
    providers = ['google', 'github']
}) => {
    return (
        <div className="space-y-3">
            {providers.includes('google') && (
                <GoogleLoginButton 
                    onLoading={onLoading}
                    disabled={disabled}
                />
            )}
            
            {providers.includes('github') && (
                <GitHubLoginButton 
                    onLoading={onLoading}
                    disabled={disabled}
                />
            )}
            
            {showDivider && (
                <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white text-gray-500">Or continue with email</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export { GoogleLoginButton, GitHubLoginButton, OAuthButtons };
export default OAuthButtons;
