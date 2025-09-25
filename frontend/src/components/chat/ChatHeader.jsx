const ChatHeader = ({ thread, onCreateNewThread }) => {
  return (
    <div className="border-b border-gray-200 bg-white px-6 py-4 flex items-center justify-between">
      <div>
        <h2 className="text-xl font-medium text-gray-800">
          {thread ? thread.title : 'New Conversation'}
        </h2>
      </div>
      
      <div className="flex items-center">
        <button
          onClick={onCreateNewThread}
          className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-gray-600 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-200"
          aria-label="New conversation"
        >
          New
        </button>
      </div>
    </div>
  );
};

export default ChatHeader;