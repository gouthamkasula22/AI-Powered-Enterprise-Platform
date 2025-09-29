import { useState } from 'react';
import { Trash2, Archive, MoreVertical } from 'lucide-react';

const ChatSidebar = ({ threads, activeThreadId, onSelectThread, onNewThread, onDeleteThread, onArchiveThread }) => {
  const [showDeleteModal, setShowDeleteModal] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteConversation = async (threadId) => {
    setIsDeleting(true);
    try {
      await onDeleteThread(threadId);
    } catch (error) {
      console.error('Error deleting conversation:', error);
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(null);
    }
  };

  const handleArchiveConversation = async (threadId) => {
    try {
      await onArchiveThread(threadId);
    } catch (error) {
      console.error('Error archiving conversation:', error);
    }
  };

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
              <li key={thread.id} className="group relative">
                <div className="flex items-center">
                  <button
                    onClick={() => onSelectThread(thread.id)}
                    className={`
                      flex items-center px-4 py-2 text-sm w-full text-left flex-1
                      ${thread.id === activeThreadId ? 'bg-gray-100 text-gray-900' : 'text-gray-700 hover:bg-gray-50'}
                    `}
                  >
                    <span className="text-gray-400 mr-3 text-sm">💬</span>
                    <span className="truncate flex-1">{thread.title}</span>
                  </button>
                  
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center pr-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleArchiveConversation(thread.id);
                      }}
                      className="p-1 text-gray-400 hover:text-yellow-600 rounded"
                      title="Archive conversation"
                    >
                      <Archive size={14} />
                    </button>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteModal(thread.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-600 rounded ml-1"
                      title="Delete conversation"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="px-4 py-3 text-sm text-gray-500">
              No conversations yet
            </li>
          )}
        </ul>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-mx mx-4">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Conversation</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete this conversation? This action cannot be undone.
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowDeleteModal(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                disabled={isDeleting}
              >
                Cancel
              </button>
              
              <button
                onClick={() => handleDeleteConversation(showDeleteModal)}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;