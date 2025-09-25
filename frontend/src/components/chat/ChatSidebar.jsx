const ChatSidebar = ({ threads, activeThreadId, onSelectThread, onNewThread }) => {
  return (
    <div className="hidden md:block w-64 border-r border-gray-200 h-full overflow-y-auto bg-white">
      <div className="p-4 border-b border-gray-200">
        <button 
          onClick={onNewThread}
          className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <span className="mr-2">+</span>
          New Chat
        </button>
      </div>
      
      <div className="py-2">
        <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Recent Conversations
        </h3>
        
        <ul className="space-y-1">
          {threads && threads.length > 0 ? (
            threads.map(thread => (
              <li key={thread.id}>
                <button
                  onClick={() => onSelectThread(thread.id)}
                  className={`
                    flex items-center px-4 py-2 text-sm w-full text-left
                    ${thread.id === activeThreadId ? 'bg-gray-100 text-gray-900' : 'text-gray-700 hover:bg-gray-50'}
                  `}
                >
                  <span className="text-gray-400 mr-3 text-sm">💬</span>
                  <span className="truncate">{thread.title}</span>
                </button>
              </li>
            ))
          ) : (
            <li className="px-4 py-3 text-sm text-gray-500">
              No conversations yet
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

export default ChatSidebar;