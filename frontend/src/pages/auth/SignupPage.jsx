import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Mail, Lock, Loader2, AlertCircle, Eye, EyeOff, Check } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export function SignupPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    termsChecked: false
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { signup } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { id, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [id]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    // Validation
    if (!formData.name.trim()) {
      setError('Full name is required.');
      return;
    }
    if (!formData.email || !/\S+@\S+\.\S+/.test(formData.email)) {
      setError('Please enter a valid email address.');
      return;
    }
    const pwdRegex = /^(?=.*[A-Z])(?=.*\d).{8,}$/;
    if (!pwdRegex.test(formData.password)) {
      setError('Password must be at least 8 characters, with 1 uppercase letter and 1 number.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (!formData.termsChecked) {
      setError('You must agree to the Terms of Service.');
      return;
    }

    setIsSubmitting(true);
    try {
      await signup(formData.name, formData.email, formData.password);
      navigate('/app/dashboard', { replace: true });
    } catch (err) {
      setError(err.message || 'Failed to create account');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4">
      <div className="w-full max-w-md my-8">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-100">Kavach</h1>
          <p className="mt-2 text-sm text-zinc-400">Create a new account</p>
        </div>

        <Card className="border-zinc-800 bg-zinc-900 shadow-md">
          <form onSubmit={handleSubmit}>
            <CardContent className="pt-6 space-y-4">
              {error && (
                <div className="flex items-center gap-2 rounded-lg bg-red-500/10 p-3 text-sm text-red-500 border border-red-500/20">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <p>{error}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="name" className="text-zinc-100">Full Name</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                  <Input 
                    id="name"
                    type="text" 
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    className="pl-9 bg-zinc-950 border-zinc-800 text-zinc-100 focus-visible:ring-indigo-500"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email" className="text-zinc-100">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                  <Input 
                    id="email"
                    type="email" 
                    placeholder="name@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    className="pl-9 bg-zinc-950 border-zinc-800 text-zinc-100 focus-visible:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-zinc-100">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                  <Input 
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    className="pl-9 pr-9 bg-zinc-950 border-zinc-800 text-zinc-100 focus-visible:ring-indigo-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-zinc-500 hover:text-zinc-300"
                    tabIndex="-1"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-zinc-100">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-zinc-500" />
                  <Input 
                    id="confirmPassword"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    className="pl-9 bg-zinc-950 border-zinc-800 text-zinc-100 focus-visible:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="termsChecked"
                  checked={formData.termsChecked}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  className="h-4 w-4 rounded border-zinc-800 bg-zinc-950 text-indigo-600 focus:ring-indigo-500"
                />
                <Label htmlFor="termsChecked" className="text-sm text-zinc-400 font-normal">
                  I agree to the Terms of Service
                </Label>
              </div>

            </CardContent>
            
            <CardFooter className="flex-col gap-4 pb-6">
              <Button 
                type="submit" 
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </Button>
              <div className="text-center text-sm text-zinc-400">
                Already have an account?{' '}
                <Link to="/login" className="font-medium text-indigo-500 hover:text-indigo-400">
                  Sign in
                </Link>
              </div>
            </CardFooter>
          </form>
        </Card>
      </div>
    </div>
  );
}
