import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { 
  ArrowRight, 
  Users, 
  PiggyBank, 
  CreditCard, 
  BarChart3,
  CheckCircle,
  TrendingUp,
  Shield,
  Sparkles,
  Star
} from 'lucide-react';

const Landing = () => {
  const stats = [
    { value: '5,000+', label: 'Active Members' },
    { value: '₦500M+', label: 'Total Savings' },
    { value: '₦1.2B+', label: 'Loans Disbursed' },
    { value: '98%', label: 'Satisfaction Rate' },
  ];

  const steps = [
    { icon: Users, title: 'Join', description: 'Register and get approved as a member' },
    { icon: PiggyBank, title: 'Contribute', description: 'Make regular contributions to build your share capital' },
    { icon: CheckCircle, title: 'Eligible', description: 'Get loan eligibility up to 3x your contributions' },
    { icon: CreditCard, title: 'Get Loan', description: 'Apply for loans with competitive interest rates' },
  ];

  const features = [
    {
      icon: PiggyBank,
      title: 'Smart Savings',
      description: 'Build your wealth through regular contributions. Every ₦10,000 equals one share in the cooperative.',
    },
    {
      icon: CreditCard,
      title: 'Quick Loans',
      description: 'Access loans up to 3x your confirmed contributions with flexible repayment terms.',
    },
    {
      icon: BarChart3,
      title: 'Real-time Dashboard',
      description: 'Track your contributions, shares, loan eligibility, and repayment status in one place.',
    },
  ];

  const testimonials = [
    {
      name: 'Adebayo Johnson',
      role: 'Business Owner',
      content: 'Bosere Cooperative helped me expand my business with a timely loan. The process was seamless!',
      image: 'https://images.unsplash.com/photo-1652702954883-622efc786f70?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxuaWdlcmlhbiUyMGJ1c2luZXNzJTIwb3duZXIlMjBzbWlsZXxlbnwwfHx8fDE3NzQzNDUxNDd8MA&ixlib=rb-4.1.0&q=85&w=100&h=100&fit=crop',
    },
    {
      name: 'Chioma Okafor',
      role: 'Market Trader',
      content: 'The cooperative culture here is amazing. I feel like part of a family that supports my financial goals.',
      image: 'https://images.unsplash.com/photo-1773858441059-d741dc584aa7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTJ8MHwxfHNlYXJjaHwxfHxhZnJpY2FuJTIwbWFya2V0JTIwd29tYW4lMjBoYXBweXxlbnwwfHx8fDE3NzQzNDUxNDh8MA&ixlib=rb-4.1.0&q=85&w=100&h=100&fit=crop',
    },
    {
      name: 'Emeka Nnamdi',
      role: 'Tech Entrepreneur',
      content: 'Transparent, efficient, and community-driven. This is what modern cooperative banking should be.',
      image: 'https://images.pexels.com/photos/10415856/pexels-photo-10415856.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=100&w=100&fit=crop',
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 hero-gradient" />
        <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1763929154533-772a384f2b31?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMzV8MHwxfHNlYXJjaHw0fHxhYnN0cmFjdCUyMGdyZWVuJTIwZ2VvbWV0cmljJTIwM2QlMjBzaGFwZXN8ZW58MHx8fHwxNzc0MzQ1MTQ5fDA&ixlib=rb-4.1.0&q=85')] bg-cover bg-center opacity-10" />
        
        <div className="relative container-app py-20 md:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-slide-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur border border-white/20">
                <Sparkles className="h-4 w-4 text-secondary" />
                <span className="text-sm text-white/90">Trusted by thousands of Nigerians</span>
              </div>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-white leading-tight tracking-tight" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Build Your Business with the Power of{' '}
                <span className="text-secondary">Cooperation</span>
              </h1>
              
              <p className="text-lg text-white/80 max-w-xl">
                Join Bosere Cooperative and unlock financial opportunities. Save together, grow together, and access loans up to 3x your contributions.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  size="lg" 
                  className="bg-secondary text-secondary-foreground hover:bg-secondary/90 btn-press h-12 px-8"
                  asChild
                  data-testid="hero-join-btn"
                >
                  <Link to="/register">
                    Join Cooperative
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button 
                  size="lg" 
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 h-12 px-8"
                  asChild
                  data-testid="hero-login-btn"
                >
                  <Link to="/login">Member Login</Link>
                </Button>
              </div>
            </div>
            
            {/* Hero Image/Stats */}
            <div className="hidden lg:block relative">
              <div className="relative z-10">
                <img 
                  src="https://images.unsplash.com/photo-1758873268663-5a362616b5a7?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1ODB8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBvZmZpY2UlMjB0ZWFtJTIwY29sbGFib3JhdGlvbnxlbnwwfHx8fDE3NzQzNDUxNDl8MA&ixlib=rb-4.1.0&q=85&w=600&h=400&fit=crop"
                  alt="Cooperative members collaborating"
                  className="rounded-2xl shadow-2xl"
                />
              </div>
              {/* Floating stats card */}
              <Card className="absolute -bottom-8 -left-8 bg-card/95 backdrop-blur shadow-xl border-border/50 z-20">
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-accent/20 flex items-center justify-center">
                      <TrendingUp className="h-6 w-6 text-accent" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold currency">₦1.2B+</p>
                      <p className="text-sm text-muted-foreground">Loans Disbursed</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-muted/30 border-y border-border">
        <div className="container-app">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <p className="text-2xl md:text-3xl font-bold text-foreground" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  {stat.value}
                </p>
                <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="landing-section" data-testid="how-it-works-section">
        <div className="container-app">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              How It Works
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Getting started with Bosere Cooperative is simple. Follow these steps to begin your journey to financial freedom.
            </p>
          </div>
          
          <div className="grid md:grid-cols-4 gap-6 stagger-children">
            {steps.map((step, index) => (
              <div key={index} className="relative">
                <Card className="bg-card border-border/50 h-full card-hover">
                  <CardContent className="p-6 text-center">
                    <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                      <step.icon className="h-7 w-7 text-primary" />
                    </div>
                    <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center text-sm font-bold">
                      {index + 1}
                    </div>
                    <h3 className="font-semibold text-lg mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>{step.title}</h3>
                    <p className="text-sm text-muted-foreground">{step.description}</p>
                  </CardContent>
                </Card>
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-1/2 -right-3 transform -translate-y-1/2">
                    <ArrowRight className="h-6 w-6 text-muted-foreground/30" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Products Section */}
      <section className="landing-section bg-muted/30" data-testid="products-section">
        <div className="container-app">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Our Products
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Everything you need to manage your finances and grow your wealth.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="bg-card border-border/50 card-hover overflow-hidden group">
                <CardContent className="p-8">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                    <feature.icon className="h-7 w-7 text-white" />
                  </div>
                  <h3 className="font-semibold text-xl mb-3" style={{ fontFamily: 'Manrope, sans-serif' }}>{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="landing-section" data-testid="trust-section">
        <div className="container-app">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-6" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Why Members Trust Us
              </h2>
              <div className="space-y-4">
                {[
                  { icon: Shield, text: 'Secure and transparent financial management' },
                  { icon: TrendingUp, text: 'Competitive interest rates on loans' },
                  { icon: Users, text: 'Community-driven decision making' },
                  { icon: CheckCircle, text: 'Quick loan approval process' },
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                      <item.icon className="h-5 w-5 text-accent" />
                    </div>
                    <p className="text-foreground">{item.text}</p>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Testimonials */}
            <div className="space-y-4">
              {testimonials.map((testimonial, index) => (
                <Card key={index} className="bg-card border-border/50">
                  <CardContent className="p-6">
                    <div className="flex gap-1 mb-3">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className="h-4 w-4 fill-secondary text-secondary" />
                      ))}
                    </div>
                    <p className="text-foreground mb-4">"{testimonial.content}"</p>
                    <div className="flex items-center gap-3">
                      <img 
                        src={testimonial.image} 
                        alt={testimonial.name}
                        className="w-10 h-10 rounded-full object-cover"
                      />
                      <div>
                        <p className="font-medium text-sm">{testimonial.name}</p>
                        <p className="text-xs text-muted-foreground">{testimonial.role}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="landing-section bg-primary relative overflow-hidden">
        <div className="container-app relative text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Ready to Start Your Journey?
          </h2>
          <p className="text-white/80 max-w-xl mx-auto mb-8">
            Join thousands of Nigerians who are building their financial future with Bosere Cooperative.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              size="lg" 
              className="bg-secondary text-secondary-foreground hover:bg-secondary/90 h-12 px-8 btn-press"
              asChild
              data-testid="cta-join-btn"
            >
              <Link to="/register">
                Get Started Today
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
            <Button 
              size="lg" 
              variant="outline" 
              className="border-white/30 text-white hover:bg-white/10 h-12 px-8"
              asChild
              data-testid="cta-calculator-btn"
            >
              <Link to="/calculator">Try Loan Calculator</Link>
            </Button>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
