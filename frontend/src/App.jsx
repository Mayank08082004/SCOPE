import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Sun, Moon, Activity, Server } from 'lucide-react';
import SimulationDashboard from './pages/SimulationDashboard';
import NetworkDashboard from './pages/NetworkDashboard';

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(true);

  // Initialize theme on mount
  useEffect(() => {
    // Check if user has a preference saved, otherwise default to dark
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'light' || (!savedTheme && !prefersDark)) {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    } else {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    }
  };

  return (
    <BrowserRouter>
      {/* Premium Global Navigation Bar */}
      <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            
            {/* Logo area */}
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center">
                <Activity className="h-5 w-5 text-primary" />
              </div>
              <span className="font-bold text-xl tracking-tight hidden sm:block">SCOPE</span>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center space-x-1 sm:space-x-4">
              <NavLink 
                to="/simulation" 
                className={({isActive}) => `
                  flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200
                  ${isActive 
                    ? 'bg-primary/10 text-primary' 
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  }
                `}
              >
                <Activity className="w-4 h-4" />
                <span className="hidden sm:inline">Simulation</span>
              </NavLink>

              <NavLink 
                to="/network" 
                className={({isActive}) => `
                  flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200
                  ${isActive 
                    ? 'bg-primary/10 text-primary' 
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                  }
                `}
              >
                <Server className="w-4 h-4" />
                <span className="hidden sm:inline">TCP Network</span>
              </NavLink>
            </div>

            {/* Actions */}
            <div className="flex items-center">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-full bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                aria-label="Toggle Theme"
              >
                {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </button>
            </div>

          </div>
        </div>
      </nav>

      {/* Page Content */}
      <main className="bg-background min-h-screen text-foreground">
        <Routes>
          <Route path="/" element={<SimulationDashboard />} />
          <Route path="/simulation" element={<SimulationDashboard />} />
          <Route path="/network" element={<NetworkDashboard />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
