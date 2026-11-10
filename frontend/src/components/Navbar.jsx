import React, { useState, useEffect } from 'react';
import { 
  Leaf, 
  LayoutDashboard, 
  ScanLine, 
  History, 
  BarChart3, 
  Info, 
  Globe, 
  User, 
  LogOut, 
  Sparkles,
  Menu,
  X
} from 'lucide-react';
import { apiService } from '../api/client';

export const JURISDICTIONS = [
  { id: 'us_epa', name: 'US (EPA Standard)', flag: '🇺🇸' },
  { id: 'eu_standard', name: 'EU (Dual System)', flag: '🇪🇺' },
  { id: 'uk_wrap', name: 'UK (WRAP Rules)', flag: '🇬🇧' },
  { id: 'india_cpcb', name: 'India (CPCB Rules)', flag: '🇮🇳' },
];

export default function Navbar({ 
  currentTab, 
  setCurrentTab, 
  selectedLocation, 
  setSelectedLocation, 
  currentUser, 
  onOpenAuth, 
  onLogout 
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [systemHealthy, setSystemHealthy] = useState(true);

  useEffect(() => {
    apiService.getHealth()
      .then(res => setSystemHealthy(res.status === 'healthy'))
      .catch(() => setSystemHealthy(false));
  }, []);

  const navLinks = [
    { id: 'landing', label: 'Home', icon: Leaf },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'analyze', label: 'Analyze Waste', icon: ScanLine, highlight: true },
    { id: 'history', label: 'History', icon: History },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'about', label: 'About', icon: Info },
  ];

  return (
    <nav className="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div 
            onClick={() => setCurrentTab('landing')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md shadow-emerald-600/20 group-hover:scale-105 transition-transform">
              <Leaf className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg text-slate-900 tracking-tight">EcoSort</span>
                <span className="text-xs font-bold px-1.5 py-0.5 rounded-md bg-emerald-100 text-emerald-800 uppercase tracking-wider">AI</span>
              </div>
              <p className="text-[10px] text-slate-400 font-medium">Smart Waste & Recycling</p>
            </div>
          </div>

          {/* Desktop Nav Items */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = currentTab === link.id;
              return (
                <button
                  key={link.id}
                  onClick={() => setCurrentTab(link.id)}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all ${
                    link.highlight
                      ? isActive
                        ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-600/30'
                        : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                      : isActive
                        ? 'bg-slate-100 text-emerald-700'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.label}</span>
                </button>
              );
            })}
          </div>

          {/* Right Action Bar */}
          <div className="hidden lg:flex items-center gap-3">
            {/* Jurisdiction Dropdown */}
            <div className="relative flex items-center bg-slate-100/80 rounded-xl px-2.5 py-1.5 border border-slate-200 text-xs">
              <Globe className="w-3.5 h-3.5 text-slate-400 mr-1.5 shrink-0" />
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="bg-transparent font-medium text-slate-700 focus:outline-none cursor-pointer pr-1"
              >
                {JURISDICTIONS.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.flag} {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Health Pulse Indicator */}
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] font-medium text-slate-600">
              <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
              <span>{systemHealthy ? 'Models Online' : 'Degraded'}</span>
            </div>

            {/* Auth / Profile */}
            {currentUser ? (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-xs">
                  {currentUser.username[0].toUpperCase()}
                </div>
                <div className="text-left">
                  <p className="text-xs font-bold text-slate-800 truncate max-w-[90px]">{currentUser.username}</p>
                  <p className="text-[10px] text-slate-400">Contributor</p>
                </div>
                <button
                  onClick={onLogout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-xl shadow-sm transition-all"
              >
                <User className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-slate-600 hover:bg-slate-100"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-2">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = currentTab === link.id;
            return (
              <button
                key={link.id}
                onClick={() => {
                  setCurrentTab(link.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold text-left transition ${
                  isActive ? 'bg-emerald-50 text-emerald-700' : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.label}</span>
              </button>
            );
          })}

          <div className="pt-4 border-t border-slate-100 flex flex-col gap-3">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>Jurisdiction:</span>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="bg-slate-100 px-2 py-1 rounded-lg text-slate-800 font-medium"
              >
                {JURISDICTIONS.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.flag} {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {currentUser ? (
              <button
                onClick={() => { onLogout(); setMobileMenuOpen(false); }}
                className="w-full py-2.5 text-center text-xs font-semibold text-rose-600 bg-rose-50 rounded-xl"
              >
                Sign Out ({currentUser.username})
              </button>
            ) : (
              <button
                onClick={() => { onOpenAuth(); setMobileMenuOpen(false); }}
                className="w-full py-2.5 text-center text-xs font-semibold text-white bg-slate-900 rounded-xl"
              >
                Sign In / Register
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}

