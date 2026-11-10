import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import AuthModal from './components/AuthModal';

import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import AnalyzePage from './pages/AnalyzePage';
import HistoryPage from './pages/HistoryPage';
import AnalyticsPage from './pages/AnalyticsPage';
import AboutPage from './pages/AboutPage';

import { apiService } from './api/client';

export default function App() {
  const [currentTab, setCurrentTab] = useState('landing');
  const [selectedLocation, setSelectedLocation] = useState('us_epa');
  const [currentUser, setCurrentUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  useEffect(() => {
    // Load persisted user if any
    const user = apiService.getCurrentUser();
    if (user) setCurrentUser(user);
  }, []);

  const handleTabChange = (tab) => {
    setCurrentTab(tab);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleLogout = () => {
    apiService.logout();
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-800">
      {/* Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={handleTabChange}
        selectedLocation={selectedLocation}
        setSelectedLocation={setSelectedLocation}
        currentUser={currentUser}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Page Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
        {currentTab === 'landing' && (
          <LandingPage onGetStarted={(tab) => handleTabChange(tab || 'analyze')} />
        )}
        {currentTab === 'dashboard' && (
          <DashboardPage onNavigate={handleTabChange} />
        )}
        {currentTab === 'analyze' && (
          <AnalyzePage defaultLocation={selectedLocation} />
        )}
        {currentTab === 'history' && (
          <HistoryPage />
        )}
        {currentTab === 'analytics' && (
          <AnalyticsPage />
        )}
        {currentTab === 'about' && (
          <AboutPage />
        )}
      </main>

      {/* Footer */}
      <Footer onNavigate={handleTabChange} />

      {/* Authentication Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={(user) => {
          setCurrentUser(user);
        }}
      />
    </div>
  );
}

