import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'

const HomePage = () => {
  const { isAuthenticated, user } = useAuth()
  const { isDarkMode } = useTheme()

  const features = [
    {
      icon: '💬',
      title: 'AI Chat Assistant',
      description: 'Powered by Claude AI for intelligent conversations',
      link: '/chat/new',
      color: isDarkMode ? 'from-orange-500/20 to-orange-600/20' : 'from-blue-50 to-blue-100',
      textColor: isDarkMode ? 'text-orange-400' : 'text-blue-600'
    },
    {
      icon: '📊',
      title: 'Excel Q&A',
      description: 'Upload spreadsheets and ask questions in natural language',
      link: '/excel',
      color: isDarkMode ? 'from-green-500/20 to-green-600/20' : 'from-green-50 to-green-100',
      textColor: isDarkMode ? 'text-green-400' : 'text-green-600'
    },
    {
      icon: '🎨',
      title: 'Image Generation',
      description: 'Create stunning AI-generated images with DALL-E',
      link: '/chat/new',
      color: isDarkMode ? 'from-purple-500/20 to-purple-600/20' : 'from-purple-50 to-purple-100',
      textColor: isDarkMode ? 'text-purple-400' : 'text-purple-600'
    },
    {
      icon: '🖼️',
      title: 'Image Gallery',
      description: 'Browse and manage your generated image collection',
      link: '/chat/new',
      color: isDarkMode ? 'from-pink-500/20 to-pink-600/20' : 'from-pink-50 to-pink-100',
      textColor: isDarkMode ? 'text-pink-400' : 'text-pink-600'
    }
  ]

  const securityFeatures = [
    {
      icon: '🔐',
      title: 'Enterprise Security',
      description: 'JWT authentication with Argon2 password hashing and email verification'
    },
    {
      icon: '🚀',
      title: 'OAuth Integration',
      description: 'Seamless login with Google, Facebook, and LinkedIn'
    },
    {
      icon: '👥',
      title: 'Role-Based Access',
      description: 'Advanced RBAC system with Super Admin, Admin, and User roles'
    },
    {
      icon: '🎯',
      title: 'Modern Tech Stack',
      description: 'React, FastAPI, PostgreSQL, Docker, and cutting-edge AI models'
    }
  ]

  return (
    <div className={`min-h-screen ${isDarkMode ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' : 'bg-gradient-to-br from-blue-50 via-white to-gray-50'}`}>
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          {/* Title */}
          <div className="mb-6">
            <h1 className={`text-5xl md:text-6xl font-bold mb-4 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
              AI-Powered Enterprise Platform
            </h1>
            <p className={`text-xl md:text-2xl ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
              Chat, Analyze, Create — All in One Secure Platform
            </p>
          </div>
          
          {isAuthenticated ? (
            <div className="space-y-6">
              <div className={`inline-flex items-center gap-3 px-6 py-3 rounded-full ${isDarkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'} shadow-lg`}>
                <div className={`w-10 h-10 rounded-full ${isDarkMode ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-100 text-blue-600'} flex items-center justify-center font-bold text-lg`}>
                  {user?.first_name?.[0] || user?.email?.[0] || 'U'}
                </div>
                <div className="text-left">
                  <p className={`text-sm font-medium ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Welcome back
                  </p>
                  <p className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                    {user?.first_name || user?.email}
                  </p>
                </div>
                <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  ['super_admin', 'SUPERADMIN', 'superadmin'].includes(user?.role) 
                    ? isDarkMode ? 'bg-purple-900/50 text-purple-400' : 'bg-purple-100 text-purple-800'
                    : ['admin', 'ADMIN'].includes(user?.role) 
                    ? isDarkMode ? 'bg-blue-900/50 text-blue-400' : 'bg-blue-100 text-blue-800'
                    : isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-100 text-gray-800'
                }`}>
                  {user?.role?.toUpperCase() || 'USER'}
                </span>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  to="/chat/new" 
                  className={`inline-flex items-center justify-center gap-2 font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 shadow-lg ${
                    isDarkMode 
                      ? 'bg-orange-600 hover:bg-orange-500 text-white' 
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  <span className="material-icons-outlined">rocket_launch</span>
                  Launch Platform
                </Link>
                
                {(['admin', 'ADMIN', 'super_admin', 'SUPERADMIN', 'superadmin'].includes(user?.role)) && (
                  <Link 
                    to="/admin" 
                    className={`inline-flex items-center justify-center gap-2 font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 ${
                      isDarkMode 
                        ? 'bg-gray-800 hover:bg-gray-700 text-white border border-gray-600' 
                        : 'bg-white hover:bg-gray-50 text-gray-900 border-2 border-gray-300'
                    }`}
                  >
                    <span className="material-icons-outlined">admin_panel_settings</span>
                    Admin Dashboard
                  </Link>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                to="/login" 
                className={`inline-flex items-center justify-center gap-2 font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 shadow-lg ${
                  isDarkMode 
                    ? 'bg-orange-600 hover:bg-orange-500 text-white' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                <span className="material-icons-outlined">login</span>
                Sign In
              </Link>
              <Link 
                to="/register" 
                className={`inline-flex items-center justify-center gap-2 font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 ${
                  isDarkMode 
                    ? 'bg-gray-800 hover:bg-gray-700 text-white border border-gray-600' 
                    : 'bg-white hover:bg-gray-50 text-blue-600 border-2 border-blue-600'
                }`}
              >
                <span className="material-icons-outlined">person_add</span>
                Create Account
              </Link>
            </div>
          )}
        </div>

        {/* AI Features Grid */}
        <div className="mt-20 max-w-6xl mx-auto">
          <h2 className={`text-3xl font-bold text-center mb-12 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Powerful AI Features
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <Link
                key={index}
                to={isAuthenticated ? feature.link : '/login'}
                className={`group p-6 rounded-2xl transition-all transform hover:scale-105 hover:shadow-2xl ${
                  isDarkMode 
                    ? 'bg-gray-800/50 border border-gray-700 hover:border-gray-600' 
                    : 'bg-white border border-gray-200 hover:shadow-xl'
                }`}
              >
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center text-3xl mb-4 group-hover:scale-110 transition-transform`}>
                  {feature.icon}
                </div>
                <h3 className={`text-xl font-bold mb-2 ${feature.textColor}`}>
                  {feature.title}
                </h3>
                <p className={`${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {feature.description}
                </p>
                <div className={`mt-4 flex items-center gap-2 text-sm font-medium ${feature.textColor}`}>
                  <span>Explore</span>
                  <span className="material-icons-outlined text-sm">arrow_forward</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Security Features */}
        <div className="mt-20 max-w-6xl mx-auto">
          <h2 className={`text-3xl font-bold text-center mb-12 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
            Built on Enterprise-Grade Security
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {securityFeatures.map((feature, index) => (
              <div
                key={index}
                className={`p-6 rounded-xl text-center ${
                  isDarkMode 
                    ? 'bg-gray-800/30 border border-gray-700' 
                    : 'bg-white/50 border border-gray-200'
                }`}
              >
                <div className="text-4xl mb-3">{feature.icon}</div>
                <h3 className={`text-lg font-semibold mb-2 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  {feature.title}
                </h3>
                <p className={`text-sm ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack Badge */}
        <div className={`mt-16 text-center py-8 px-4 rounded-2xl ${
          isDarkMode 
            ? 'bg-gradient-to-r from-gray-800/50 to-gray-900/50 border border-gray-700' 
            : 'bg-gradient-to-r from-gray-50 to-white border border-gray-200'
        }`}>
          <p className={`text-sm font-medium mb-3 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`}>
            POWERED BY
          </p>
          <div className={`flex flex-wrap justify-center gap-4 text-sm font-semibold ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
            <span>React</span>
            <span>•</span>
            <span>FastAPI</span>
            <span>•</span>
            <span>PostgreSQL</span>
            <span>•</span>
            <span>Claude AI</span>
            <span>•</span>
            <span>DALL-E</span>
            <span>•</span>
            <span>Docker</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage
