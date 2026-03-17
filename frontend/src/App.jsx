import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { SpeedInsights } from '@vercel/speed-insights/react';
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Login';

// Main Pages
import Dashboard from './pages/Dashboard';
import DocumentScanner from './pages/DocumentScanner';
import Compliance from './pages/Compliance';
import SubsidyExplorer from './pages/SubsidyExplorer';
import NegotiationCenter from './pages/NegotiationCenter';
import Chat from './pages/Chat';
import History from './pages/History';
import Subsidies from './pages/Subsidies';
import Settings from './pages/Settings';

// Admin Imports
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import SuperAdminDashboard from './pages/admin/SuperAdminDashboard';
import TermsOfService from './pages/TermsOfService';
import PrivacyPolicy from './pages/PrivacyPolicy';

// Auth check helper
const isAuthenticated = () => {
  const token = localStorage.getItem('token');
  return !!token;
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const auth = isAuthenticated();

  if (!auth) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <SpeedInsights />
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/terms" element={<TermsOfService />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />

        {/* Protected User Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="scanner" element={<DocumentScanner />} />
          <Route path="compliance" element={<Compliance />} />
          <Route path="subsidies" element={<SubsidyExplorer />} />
          <Route path="negotiation" element={<NegotiationCenter />} />
          <Route path="chat" element={<Chat />} />
          <Route path="history" element={<History />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Admin Routes - MUST be before catch-all */}
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<SuperAdminDashboard />} />
        <Route path="/admin" element={<Navigate to="/admin/login" replace />} />

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
