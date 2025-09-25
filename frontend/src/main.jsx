import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import AppTest from './AppTest.jsx'  // Import test app
import './index.css'

// Use TEST_MODE to toggle between production and test app
const TEST_MODE = false;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {TEST_MODE ? <AppTest /> : <App />}
  </React.StrictMode>,
)
