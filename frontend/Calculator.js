import { useState } from 'react';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { formatCurrency } from '../lib/utils';
import { Calculator, TrendingUp, Calendar, Percent, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Link } from 'react-router-dom';

const PublicCalculator = () => {
  const [amount, setAmount] = useState(100000);
  const [duration, setDuration] = useState(12);
  const [contributionTotal, setContributionTotal] = useState(100000);

  const interestRate = 5; // 5% per annum
  const maxLoan = contributionTotal * 3;
  const isEligible = amount <= maxLoan;

  // Calculate loan payment
  const monthlyRate = interestRate / 100 / 12;
  const monthlyPayment = amount * (monthlyRate * Math.pow(1 + monthlyRate, duration)) / (Math.pow(1 + monthlyRate, duration) - 1);
  const totalRepayment = monthlyPayment * duration;
  const totalInterest = totalRepayment - amount;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="container-app py-12 md:py-20">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-3xl md:text-4xl font-bold mb-4" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Loan Calculator
            </h1>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Calculate your potential loan amount and monthly repayments. Your loan eligibility is 3x your total confirmed contributions.
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8">
            {/* Input Card */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  <Calculator className="h-5 w-5 text-primary" />
                  Calculate Your Loan
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Contribution Total */}
                <div className="form-group">
                  <Label>Your Total Contributions (₦)</Label>
                  <Input
                    type="number"
                    value={contributionTotal}
                    onChange={(e) => setContributionTotal(parseFloat(e.target.value) || 0)}
                    className="h-11"
                    data-testid="public-contribution-input"
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    Max eligible loan: <span className="font-semibold currency">{formatCurrency(maxLoan)}</span>
                  </p>
                </div>

                {/* Loan Amount */}
                <div className="form-group">
                  <div className="flex justify-between items-center mb-2">
                    <Label>Loan Amount</Label>
                    <span className="text-lg font-bold currency">{formatCurrency(amount)}</span>
                  </div>
                  <Slider
                    value={[amount]}
                    onValueChange={(value) => setAmount(value[0])}
                    min={10000}
                    max={Math.max(maxLoan, 100000)}
                    step={10000}
                    className="py-4"
                    data-testid="public-amount-slider"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{formatCurrency(10000)}</span>
                    <span>{formatCurrency(Math.max(maxLoan, 100000))}</span>
                  </div>
                </div>

                {/* Duration */}
                <div className="form-group">
                  <div className="flex justify-between items-center mb-2">
                    <Label>Repayment Duration</Label>
                    <span className="text-lg font-bold">{duration} months</span>
                  </div>
                  <Slider
                    value={[duration]}
                    onValueChange={(value) => setDuration(value[0])}
                    min={3}
                    max={24}
                    step={3}
                    className="py-4"
                    data-testid="public-duration-slider"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>3 months</span>
                    <span>24 months</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Result Card */}
            <Card className={isEligible ? 'border-accent/50' : 'border-destructive/50'}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
                  <TrendingUp className="h-5 w-5 text-accent" />
                  Repayment Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {/* Eligibility Status */}
                  <div className={`p-4 rounded-lg ${isEligible ? 'bg-accent/10' : 'bg-destructive/10'}`}>
                    <p className={`font-medium ${isEligible ? 'text-accent' : 'text-destructive'}`}>
                      {isEligible 
                        ? '✓ You would be eligible for this loan' 
                        : `✗ Amount exceeds eligibility (Max: ${formatCurrency(maxLoan)})`}
                    </p>
                  </div>

                  {/* Monthly Payment */}
                  <div className="text-center py-4 border-b border-border">
                    <p className="text-sm text-muted-foreground mb-1">Monthly Payment</p>
                    <p className="text-4xl font-bold currency text-primary">
                      {formatCurrency(isNaN(monthlyPayment) ? 0 : monthlyPayment)}
                    </p>
                  </div>

                  {/* Details Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <TrendingUp className="h-4 w-4" />
                        <span className="text-sm">Principal</span>
                      </div>
                      <p className="text-lg font-semibold currency">{formatCurrency(amount)}</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Percent className="h-4 w-4" />
                        <span className="text-sm">Interest Rate</span>
                      </div>
                      <p className="text-lg font-semibold">{interestRate}% p.a.</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Calendar className="h-4 w-4" />
                        <span className="text-sm">Duration</span>
                      </div>
                      <p className="text-lg font-semibold">{duration} months</p>
                    </div>
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <TrendingUp className="h-4 w-4" />
                        <span className="text-sm">Total Interest</span>
                      </div>
                      <p className="text-lg font-semibold currency">
                        {formatCurrency(isNaN(totalInterest) ? 0 : totalInterest)}
                      </p>
                    </div>
                  </div>

                  {/* Total */}
                  <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">Total Repayment</span>
                      <span className="text-2xl font-bold currency">
                        {formatCurrency(isNaN(totalRepayment) ? 0 : totalRepayment)}
                      </span>
                    </div>
                  </div>

                  {/* CTA */}
                  <Button asChild className="w-full" data-testid="calculator-join-btn">
                    <Link to="/register">
                      Join to Get Started
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Info Card */}
          <Card className="mt-8 bg-muted/30">
            <CardContent className="p-6">
              <h3 className="font-semibold mb-3" style={{ fontFamily: 'Manrope, sans-serif' }}>
                How Loan Eligibility Works
              </h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm text-muted-foreground">
                <ul className="space-y-2">
                  <li>• Your maximum loan amount is <strong>3x your confirmed contributions</strong></li>
                  <li>• Only admin-approved contributions count towards eligibility</li>
                  <li>• Interest is calculated at <strong>5% per annum</strong></li>
                </ul>
                <ul className="space-y-2">
                  <li>• You can only have one active loan at a time</li>
                  <li>• Repayments can be deducted from future contributions</li>
                  <li>• ₦10,000 contribution = 1 Share in the cooperative</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default PublicCalculator;
