import { useState } from 'react';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';
import ContextPanel from './ContextPanel';

const DashboardLayout = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isContextPanelOpen, setIsContextPanelOpen] = useState(false);
  const [contextPanelContent, setContextPanelContent] = useState(null);
  
  const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
  const toggleContextPanel = () => setIsContextPanelOpen(!isContextPanelOpen);
  
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={isSidebarOpen} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <TopNavbar 
          onMenuClick={toggleSidebar} 
          onContextPanelClick={toggleContextPanel}
        />
        <main className="flex-1 overflow-y-auto p-0 bg-gray-50">
          <div className="h-full max-w-6xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
      <ContextPanel 
        isOpen={isContextPanelOpen}
        onClose={toggleContextPanel}
        content={contextPanelContent}
      />
    </div>
  );
};

export default DashboardLayout;