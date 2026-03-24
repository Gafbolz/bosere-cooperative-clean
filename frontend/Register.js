import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Navbar } from '../components/layout/Navbar';
import { toast } from 'sonner';
import { Eye, EyeOff, Loader2, CheckCircle } from 'lucide-react';

const Register = () => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setLoading(true);

    try {
      const { confirmPassword, ...userData } = formData;
      await register(userData);
      toast.success('Welcome to Bosere Cooperative! Your account is pending approval.');
      navigate('/dashboard');
    } catch (error) {
      console.error('Registration error:', error);
      const message = error.message || error.response?.data?.detail || 'Registration failed. Please try again.';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const benefits = [
    'Access to loans up to 3x your contributions',
    'Flexible repayment options',
    'Community-driven financial support',
    'Transparent fee structure'
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container-app py-12 md:py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-start max-w-5xl mx-auto">
          {/* Benefits Section */}
          <div className="hidden lg:block">
            <h1 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Join Bosere Cooperative Today
            </h1>
            <p className="text-muted-foreground mb-8">
              Take the first step towards financial freedom. Join our community of members building wealth together.
            </p>
            
            <div className="space-y-4">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-3">
                  <div className="w-6 h-6 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <CheckCircle className="h-4 w-4 text-accent" />
                  </div>
                  <p className="text-foreground">{benefit}</p>
                </div>
              ))}
            </div>

            <div className="mt-8 p-6 rounded-xl bg-primary/5 border border-primary/10">
              <h3 className="font-semibold mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                How Shares Work
              </h3>
              <p className="text-sm text-muted-foreground">
                Every ₦10,000 contribution equals 1 share in the cooperative. Your shares determine your voting power and loan eligibility.
              </p>
            </div>

            <div className="mt-4 p-6 rounded-xl bg-accent/5 border border-accent/10">
              <h3 className="font-semibold mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Powered by Supabase
              </h3>
              <p className="text-sm text-muted-foreground">
                Your data is securely stored in PostgreSQL with enterprise-grade security and authentication.
              </p>
            </div>
          </div>

          {/* Registration Form */}
          <Card className="border-border/50 shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Create Account
              </CardTitle>
              <CardDescription>
                Fill in your details to join the cooperative
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="form-group">
                  <Label htmlFor="full_name" className="form-label">Full Name</Label>
                  <Input
                    id="full_name"
                    name="full_name"
                    placeholder="John Doe"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                    className="h-11"
                    data-testid="register-name-input"
                  />
                </div>

                <div className="form-group">
                  <Label htmlFor="email" className="form-label">Email</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="h-11"
                    data-testid="register-email-input"
                  />
                </div>

                <div className="form-group">
                  <Label htmlFor="phone" className="form-label">Phone Number</Label>
                  <Input
                    id="phone"
                    name="phone"
                    type="tel"
                    placeholder="+234 800 000 0000"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                    className="h-11"
                    data-testid="register-phone-input"
                  />
                </div>
                
                <div className="form-group">
                  <Label htmlFor="password" className="form-label">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="Min. 6 characters"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      className="h-11 pr-10"
                      data-testid="register-password-input"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="form-group">
                  <Label htmlFor="confirmPassword" className="form-label">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    className="h-11"
                    data-testid="register-confirm-password-input"
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-11" 
                  disabled={loading}
                  data-testid="register-submit-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating Account...
                    </>
                  ) : (
                    'Join Cooperative'
                  )}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-muted-foreground">
                Already have an account?{' '}
                <Link to="/login" className="text-primary hover:underline font-medium" data-testid="login-link">
                  Sign in
                </Link>
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Register;
