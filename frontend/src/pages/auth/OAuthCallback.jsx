import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import toast from 'react-hot-toast';

const OAuthCallback = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const { login } = useAuth();
    const [isProcessing, setIsProcessing] = useState(true);
    const [status, setStatus] = useState('Processing authentication...');
    const processedRef = useRef(false); // Prevent multiple processing

    useEffect(() => {
        // Prevent multiple processing of the same callback
        if (processedRef.current) return;
        processedRef.current = true;

        const processOAuthCallback = async () => {
            try {
                // Check for error parameters
                const error = searchParams.get('error');
                const errorDescription = searchParams.get('error_description');

                if (error) {
                    console.error('OAuth Error:', error, errorDescription);
                    setStatus('Authentication failed');
                    toast.error(errorDescription || 'OAuth authentication failed');
                    
                    setTimeout(() => {
                        navigate('/login');
                    }, 3000);
                    return;
                }

                // Extract success parameters
                const success = searchParams.get('success');
                const accessToken = searchParams.get('access_token');
                const refreshToken = searchParams.get('refresh_token');
                const userId = searchParams.get('user_id');
                const email = searchParams.get('email');
                const displayName = searchParams.get('display_name');
                const isNewUser = searchParams.get('is_new_user') === 'true';
                const provider = searchParams.get('provider');

                if (!success || !accessToken || !refreshToken || !userId) {
                    console.error('Missing required OAuth parameters');
                    setStatus('Invalid authentication response');
                    toast.error('Invalid authentication response');
                    
                    setTimeout(() => {
                        navigate('/login');
                    }, 3000);
                    return;
                }

                setStatus('Completing authentication...');

                // Create user object for AuthContext
                const user = {
                    id: userId,
                    email: email,
                    display_name: displayName || email,
                    first_name: null,
                    last_name: null,
                    profile_picture_url: null,
                    is_verified: true, // OAuth users are verified
                    is_active: true
                };

                // Create tokens object
                const tokens = {
                    access_token: accessToken,
                    refresh_token: refreshToken,
                    token_type: 'bearer'
                };

                // Use the login method from AuthContext to set user state (without showing toast)
                const result = await login({ user, tokens });
                
                if (result.success) {
                    // Show success message only once
                    if (isNewUser) {
                        toast.success(`Welcome! Your account has been created using ${provider?.charAt(0).toUpperCase() + provider?.slice(1)}.`);
                    } else {
                        toast.success(`Welcome back! Signed in with ${provider?.charAt(0).toUpperCase() + provider?.slice(1)}.`);
                    }

                    setStatus('Authentication successful! Redirecting...');

                    // Redirect to the return URL or chat page
                    const returnUrl = localStorage.getItem('oauth_return_url');
                    localStorage.removeItem('oauth_return_url');
                    
                    setTimeout(() => {
                        navigate(returnUrl || '/chat/new');
                    }, 1500);
                } else {
                    throw new Error('Login failed');
                }

            } catch (error) {
                console.error('OAuth callback processing error:', error);
                setStatus('Authentication processing failed');
                toast.error('Failed to process authentication');
                
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
            } finally {
                setIsProcessing(false);
            }
        };

        processOAuthCallback();
    }, []); // Empty dependency array, process only once

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8">
                <div className="text-center">
                    <div className="mx-auto flex items-center justify-center h-24 w-24 rounded-full bg-blue-100">
                        {isProcessing ? (
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                        ) : (
                            <svg 
                                className="h-12 w-12 text-blue-600" 
                                fill="none" 
                                stroke="currentColor" 
                                viewBox="0 0 24 24"
                            >
                                <path 
                                    strokeLinecap="round" 
                                    strokeLinejoin="round" 
                                    strokeWidth={2} 
                                    d="M5 13l4 4L19 7" 
                                />
                            </svg>
                        )}
                    </div>
                    
                    <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                        {isProcessing ? 'Authenticating' : 'Authentication Complete'}
                    </h2>
                    
                    <p className="mt-2 text-sm text-gray-600">
                        {status}
                    </p>
                    
                    {isProcessing && (
                        <div className="mt-4">
                            <div className="animate-pulse flex space-x-1 justify-center">
                                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                                <div className="h-2 w-2 bg-blue-600 rounded-full"></div>
                            </div>
                        </div>
                    )}
                    
                    {!isProcessing && (
                        <div className="mt-4">
                            <p className="text-xs text-gray-500">
                                You will be redirected automatically...
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OAuthCallback;
