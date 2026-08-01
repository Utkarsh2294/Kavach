import { Outlet, Link } from 'react-router-dom';
import { Shield, Menu } from 'lucide-react';

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans">
      <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-indigo-500" />
            <span className="font-bold text-xl tracking-tight">Kavach</span>
          </Link>
          
          <nav className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Features</a>
            <Link to="/login" className="text-sm font-medium text-zinc-400 hover:text-zinc-100 transition-colors">Login</Link>
            <Link to="/signup" className="text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors">
              Sign Up
            </Link>
          </nav>
          
          <button className="md:hidden text-zinc-400 hover:text-zinc-100">
            <Menu className="h-6 w-6" />
          </button>
        </div>
      </header>
      
      <main className="flex-1 flex flex-col p-6">
        <Outlet />
      </main>
      
      <footer className="border-t border-zinc-800 bg-zinc-950 py-12">
        <div className="container mx-auto px-4 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-zinc-500" />
            <span className="font-semibold text-zinc-500">Kavach</span>
            <span className="text-zinc-600 text-sm ml-2">Enterprise AI Governance</span>
          </div>
          
          <div className="flex gap-6 text-sm text-zinc-500">
            <Link to="/about" className="hover:text-zinc-300 transition-colors">About</Link>
            <a href="#features" className="hover:text-zinc-300 transition-colors">Features</a>
            <Link to="/security" className="hover:text-zinc-300 transition-colors">Security</Link>
            <Link to="/contact" className="hover:text-zinc-300 transition-colors">Contact</Link>
          </div>
          
          <div className="text-sm text-zinc-600">
            &copy; 2025 Kavach. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
