import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '98.css'
import './index.css'
import App from './App.tsx'
import { ErrorProvider } from './context/ErrorContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorProvider>
      <App />
    </ErrorProvider>
  </StrictMode>,
)
