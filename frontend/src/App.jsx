import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Login';
import Chat from './pages/Chat';
import History from './pages/History';
import Subsidies from './pages/Subsidies';
import Settings from './pages/Settings';

function App() {
  // Mock authentication state
  const isAuthenticated = true; // Set to true for demo, toggle to check login page

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Protected Routes */}
        <Route element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" replace />}>
          <Route path="/" element={<Chat />} />
          <Route path="/history" element={<History />} />
          <Route path="/subsidies" element={<Subsidies />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
