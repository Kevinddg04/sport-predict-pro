import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#1a2235',
            color: '#f9fafb',
            border: '1px solid #2d3748',
          },
          success: { iconTheme: { primary: '#00d68f', secondary: '#0a0e1a' } },
          error:   { iconTheme: { primary: '#ef4444', secondary: '#0a0e1a' } },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
