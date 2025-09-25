const ContextPanel = ({ isOpen, onClose, content }) => {
  return (
    <div 
      className={`
        fixed inset-y-0 right-0 z-20 w-80 bg-white border-l border-gray-200
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        md:static md:translate-x-0 md:transition-none
        ${isOpen ? 'md:w-80' : 'md:w-0'}
      `}
    >
      <div className="h-16 border-b border-gray-200 flex items-center justify-between px-4">
        <h3 className="text-lg font-medium text-gray-900">Details</h3>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 focus:outline-none"
          aria-label="Close panel"
        >
          <span className="material-icons-outlined">close</span>
        </button>
      </div>
      
      <div className="p-4 overflow-y-auto h-[calc(100%-4rem)]">
        {content || (
          <div className="text-center text-gray-500 mt-8">
            <p>Select an item to view details</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContextPanel;