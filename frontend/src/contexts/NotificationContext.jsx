import { createContext, useContext, useState, useEffect } from 'react'

const NotificationContext = createContext()

export const useNotifications = () => {
  const context = useContext(NotificationContext)
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider')
  }
  return context
}

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([])
  const [unreadCount, setUnreadCount] = useState(0)

  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now(),
      timestamp: new Date(),
      read: false,
      ...notification
    }
    setNotifications(prev => [newNotification, ...prev])
    setUnreadCount(prev => prev + 1)
  }

  const markAsRead = (id) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }

  const markAllAsRead = () => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    )
    setUnreadCount(0)
  }

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id))
    setUnreadCount(prev => {
      const notification = notifications.find(n => n.id === id)
      return notification && !notification.read ? prev - 1 : prev
    })
  }

  // Simulate receiving security alerts (in real app, this would be via WebSocket/SSE)
  useEffect(() => {
    // Demo notification for testing
    const timer = setTimeout(() => {
      addNotification({
        type: 'security',
        title: 'New Device Login',
        message: 'Login detected from a new device. Was this you?'
      })
    }, 5000)

    return () => clearTimeout(timer)
  }, [])

  const value = {
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification
  }

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  )
}
