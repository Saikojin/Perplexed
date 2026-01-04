import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AuthPage from "./pages/AuthPage";
import GamePage from "./pages/GamePage";
import LeaderboardPage from "./pages/LeaderboardPage";
import SettingsPage from "./pages/SettingsPage";
import { Toaster } from "@/components/ui/sonner";

// Helper to convert hex to HSL for Tailwind variables
function hexToHSL(hex) {
  let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;
  let r = parseInt(result[1], 16);
  let g = parseInt(result[2], 16);
  let b = parseInt(result[3], 16);
  r /= 255; g /= 255; b /= 255;
  let max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, l = (max + min) / 2;
  if (max === min) {
    h = s = 0; // achromatic
  } else {
    let d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  s = Math.round(s * 100);
  l = Math.round(l * 100);
  h = Math.round(h * 360);
  return `${h} ${s}% ${l}%`;
}

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.id) setUser(data);
          setLoading(false);
        })
        .catch(() => {
          localStorage.removeItem('token');
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // Apply User Theme Settings
  useEffect(() => {
    const root = document.documentElement;
    if (user?.settings) {
      if (user.settings.ui_color_primary) {
        const hsl = hexToHSL(user.settings.ui_color_primary);
        if (hsl) root.style.setProperty('--primary', hsl);
      } else {
        root.style.removeProperty('--primary');
      }

      if (user.settings.ui_color_accent) {
        const hsl = hexToHSL(user.settings.ui_color_accent);
        if (hsl) root.style.setProperty('--accent', hsl);
      } else {
        root.style.removeProperty('--accent');
      }

      if (user.settings.background_url) {
        root.style.setProperty('--app-bg', `url('${user.settings.background_url}')`);
      } else if (user.settings.ui_color_primary) {
        // Create a gradient based on primary color
        root.style.setProperty('--app-bg', `linear-gradient(135deg, ${user.settings.ui_color_primary} 0%, #000000 100%)`);
      } else {
        root.style.removeProperty('--app-bg');
      }
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster position="top-center" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={!user ? <AuthPage setUser={setUser} /> : <Navigate to="/game" />} />
          <Route path="/game" element={user ? <GamePage user={user} setUser={setUser} /> : <Navigate to="/auth" />} />
          <Route path="/leaderboard" element={user ? <LeaderboardPage user={user} /> : <Navigate to="/auth" />} />
          <Route path="/settings" element={user ? <SettingsPage user={user} setUser={setUser} /> : <Navigate to="/auth" />} />
          <Route path="/" element={<Navigate to={user ? "/game" : "/auth"} />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;