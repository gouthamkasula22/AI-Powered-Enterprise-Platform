// Dashboard page - Claude-like layout will be implemented in Milestone 3
const DashboardPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar - 25% width */}
      <div className="w-1/4 bg-white border-r border-gray-200 p-4">
        <div className="text-center">
          <h3 className="text-lg font-semibold mb-4">Dashboard Sidebar</h3>
          <p className="text-gray-600 text-sm">
            Claude-like interface will be implemented in Milestone 3
          </p>
        </div>
      </div>

      {/* Main Content - 75% width */}
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            Welcome to Dashboard
          </h1>
          <div className="card">
            <p className="text-gray-600">
              Main dashboard content with chat-like interface will be implemented in Milestone 3
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage
