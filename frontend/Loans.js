import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Progress } from '../../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { formatCurrency, formatDate, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';
import { Plus, CreditCard, Loader2, Calculator, AlertCircle, Banknote } from 'lucide-react';

const Loans = () => {
  const { api, user } = useAuth();
  const [loans, setLoans] = useState([]);
  const [stats, setStats] = useState(null);
  const [eligibility, setEligibility] = useState(null);
  const [guarantors, setGuarantors] = useState([]);
  const [selectedGuarantor, setSelectedGuarantor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [repaymentDialogOpen, setRepaymentDialogOpen] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState(null);
  const [calculationResult, setCalculationResult] = useState(null);
  const [formData, setFormData] = useState({
    amount: '',
    duration_months: '12',
    purpose: '',
    guarantor_id: '',
    relationship_to_guarantor: ''
  });
  const [repaymentData, setRepaymentData] = useState({
    amount: '',
    notes: ''
  });

  const fetchData = async () => {
    try {
      const [loansRes, statsRes, eligibilityRes, guarantorsRes] = await Promise.all([
        api.get('/loans'),
        api.get('/dashboard/stats'),
        api.get('/eligibility').catch(() => ({ data: null })),
        api.get('/guarantor/available').catch(() => ({ data: { guarantors: [] } }))
      ]);
      setLoans(loansRes.data);
      setStats(statsRes.data);
      setEligibility(eligibilityRes.data);
      
      // Set available guarantors for the dropdown
      if (guarantorsRes.data?.guarantors) {
        setGuarantors(guarantorsRes.data.guarantors);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast.error('Failed to load loan data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [api]);

  useEffect(() => {
    if (formData.amount && formData.duration_months && stats) {
      const amount = parseFloat(formData.amount);
      const duration = parseInt(formData.duration_months);
      if (!isNaN(amount) && amount > 0) {
        calculateLoan(amount, duration);
      }
    } else {
      setCalculationResult(null);
    }
  }, [formData.amount, formData.duration_months, stats]);

  const calculateLoan = async (amount, duration) => {
    try {
      const response = await api.get('/loans/calculator', {
        params: {
          amount,
          duration_months: duration,
          contribution_total: stats?.confirmed_contributions || 0
        }
      });
      setCalculationResult(response.data);
    } catch (error) {
      console.error('Failed to calculate loan:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user?.is_approved) {
      toast.error('Your account must be approved to apply for loans');
      return;
    }

    if (!eligibility?.eligible) {
      toast.error('You are not eligible for a loan. Please check eligibility requirements.');
      return;
    }

    const amount = parseFloat(formData.amount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (amount > eligibility.loan_limit) {
      toast.error(`Amount exceeds your loan limit of ${formatCurrency(eligibility.loan_limit)}`);
      return;
    }

    // In test mode, guarantor is optional
    if (!formData.guarantor_id && !eligibility?.test_mode) {
      toast.error('Please select a guarantor');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/loans/apply', {
        amount,
        duration_months: parseInt(formData.duration_months),
        purpose: formData.purpose,
        guarantor_id: formData.guarantor_id,
        relationship_to_guarantor: formData.relationship_to_guarantor
      });
      toast.success('Loan application submitted successfully');
      setDialogOpen(false);
      setFormData({ amount: '', duration_months: '12', purpose: '', guarantor_id: '', relationship_to_guarantor: '' });
      setCalculationResult(null);
      setSelectedGuarantor(null);
      fetchData();
    } catch (error) {
      const detail = error.message || 'Failed to submit loan application';
      if (typeof detail === 'object' && detail.reasons) {
        toast.error(detail.reasons.join('. '));
      } else {
        toast.error(detail);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleRepayment = async (e) => {
    e.preventDefault();
    
    const amount = parseFloat(repaymentData.amount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/loans/${selectedLoan.id}/repayments`, {
        amount,
        notes: repaymentData.notes
      });
      toast.success('Repayment recorded successfully');
      setRepaymentDialogOpen(false);
      setRepaymentData({ amount: '', notes: '' });
      setSelectedLoan(null);
      fetchData();
    } catch (error) {
      const message = error.message || 'Failed to record repayment';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const openRepaymentDialog = (loan) => {
    setSelectedLoan(loan);
    setRepaymentDialogOpen(true);
  };

  const activeLoan = loans.find(l => ['pending', 'approved', 'active'].includes(l.status));
  const hasActiveLoan = !!activeLoan;

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="loans-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Loans
            </h1>
            <p className="text-muted-foreground">
              Apply and manage your cooperative loans
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button disabled={hasActiveLoan} data-testid="apply-loan-btn">
                <Plus className="mr-2 h-4 w-4" />
                Apply for Loan
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                  Loan Application
                </DialogTitle>
                <DialogDescription>
                  You can borrow up to {formatCurrency(stats?.loan_eligibility || 0)} (3x your confirmed contributions)
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="form-group">
                  <Label htmlFor="amount">Loan Amount (₦)</Label>
                  <Input
                    id="amount"
                    type="number"
                    min="10000"
                    step="1000"
                    max={stats?.loan_eligibility || 0}
                    placeholder="100000"
                    value={formData.amount}
                    onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                    required
                    className="h-11"
                    data-testid="loan-amount-input"
                  />
                </div>

                <div className="form-group">
                  <Label htmlFor="duration">Repayment Duration</Label>
                  <Select 
                    value={formData.duration_months} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, duration_months: value }))}
                  >
                    <SelectTrigger className="h-11" data-testid="loan-duration-select">
                      <SelectValue placeholder="Select duration" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3">3 Months</SelectItem>
                      <SelectItem value="6">6 Months</SelectItem>
                      <SelectItem value="12">12 Months</SelectItem>
                      <SelectItem value="18">18 Months</SelectItem>
                      <SelectItem value="24">24 Months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="form-group">
                  <Label htmlFor="purpose">Purpose of Loan</Label>
                  <Textarea
                    id="purpose"
                    placeholder="Business expansion, emergency, etc."
                    value={formData.purpose}
                    onChange={(e) => setFormData(prev => ({ ...prev, purpose: e.target.value }))}
                    required
                    rows={3}
                    data-testid="loan-purpose-input"
                  />
                </div>

                {/* Guarantor Selection */}
                <div className="form-group space-y-3">
                  <Label>Select Guarantor <span className="text-red-500">*</span></Label>
                  
                  {/* Proper dropdown selection */}
                  <Select
                    value={formData.guarantor_id}
                    onValueChange={(value) => {
                      const selected = guarantors.find(g => g.id === value);
                      setSelectedGuarantor(selected);
                      setFormData(prev => ({ ...prev, guarantor_id: value }));
                    }}
                  >
                    <SelectTrigger className="h-11" data-testid="guarantor-select">
                      <SelectValue placeholder="Select a guarantor from the list" />
                    </SelectTrigger>
                    <SelectContent>
                      {guarantors.length === 0 ? (
                        <div className="p-3 text-sm text-muted-foreground text-center">
                          {eligibility?.test_mode 
                            ? "Loading guarantors..." 
                            : "No eligible guarantors found"}
                        </div>
                      ) : (
                        guarantors.map((g) => (
                          <SelectItem 
                            key={g.id} 
                            value={g.id}
                            disabled={!g.is_valid_guarantor}
                          >
                            <div className="flex items-center gap-2">
                              <span>{g.full_name}</span>
                              <span className="text-xs text-muted-foreground">({g.email})</span>
                              {!g.is_valid_guarantor && (
                                <Badge variant="destructive" className="text-xs">Ineligible</Badge>
                              )}
                            </div>
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  
                  {/* Show selected guarantor info */}
                  {selectedGuarantor && (
                    <Card className="bg-accent/10 border-accent/30">
                      <CardContent className="p-3">
                        <div className="flex justify-between items-center">
                          <div>
                            <p className="font-medium">{selectedGuarantor.full_name}</p>
                            <p className="text-xs text-muted-foreground">{selectedGuarantor.email}</p>
                            <p className="text-xs text-muted-foreground">Credit Score: {selectedGuarantor.credit_score || 50}</p>
                            {selectedGuarantor.test_mode && (
                              <Badge className="mt-1 bg-yellow-500/20 text-yellow-400 text-xs">TEST MODE</Badge>
                            )}
                          </div>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedGuarantor(null);
                              setFormData(prev => ({ ...prev, guarantor_id: '' }));
                            }}
                          >
                            Clear
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                  
                  {/* Test mode indicator */}
                  {eligibility?.test_mode && (
                    <p className="text-xs text-yellow-500">
                      ⚠️ TEST MODE: All users are available as guarantors
                    </p>
                  )}
                </div>

                <div className="form-group">
                  <Label htmlFor="relationship">Relationship to Guarantor</Label>
                  <Select 
                    value={formData.relationship_to_guarantor} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, relationship_to_guarantor: value }))}
                  >
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="Select relationship" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="family">Family Member</SelectItem>
                      <SelectItem value="friend">Friend</SelectItem>
                      <SelectItem value="colleague">Colleague</SelectItem>
                      <SelectItem value="business_partner">Business Partner</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {calculationResult && (
                  <Card className={`${calculationResult.is_eligible ? 'bg-accent/10 border-accent/30' : 'bg-destructive/10 border-destructive/30'}`}>
                    <CardContent className="p-4 space-y-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Calculator className="h-4 w-4" />
                        <span className="font-medium">Repayment Breakdown</span>
                      </div>
                      {!calculationResult.is_eligible && (
                        <div className="flex items-center gap-2 text-destructive text-sm mb-2">
                          <AlertCircle className="h-4 w-4" />
                          <span>Amount exceeds eligibility of {formatCurrency(calculationResult.max_eligible_loan)}</span>
                        </div>
                      )}
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <p className="text-muted-foreground">Monthly Payment</p>
                          <p className="font-semibold currency">{formatCurrency(calculationResult.monthly_payment)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Total Repayment</p>
                          <p className="font-semibold currency">{formatCurrency(calculationResult.total_repayment)}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Interest Rate</p>
                          <p className="font-semibold">{calculationResult.interest_rate}% p.a.</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Total Interest</p>
                          <p className="font-semibold currency">{formatCurrency(calculationResult.total_interest)}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={submitting || (calculationResult && !calculationResult.is_eligible)}
                  data-testid="submit-loan-btn"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Application'
                  )}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Summary Cards */}
        <div className="grid sm:grid-cols-4 gap-4">
          <Card className={`stat-card ${eligibility?.eligible ? 'border-green-500/30' : 'border-red-500/30'}`}>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Eligibility Status</p>
              <div className="flex items-center gap-2">
                {eligibility?.eligible ? (
                  <>
                    <Badge className="bg-green-500/20 text-green-400">Eligible</Badge>
                    <span className="text-lg font-bold">{eligibility?.multiplier || 0}x</span>
                  </>
                ) : (
                  <Badge className="bg-red-500/20 text-red-400">Not Eligible</Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {eligibility?.membership_months || 0} months membership
              </p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Loan Limit</p>
              <p className="text-2xl font-bold currency">{formatCurrency(eligibility?.loan_limit || 0)}</p>
              <p className="text-xs text-muted-foreground mt-1">Based on savings & tier</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Active Loan</p>
              <p className="text-2xl font-bold currency">{formatCurrency(stats?.active_loan_amount || 0)}</p>
              {stats?.active_loan_amount > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {formatCurrency(stats?.active_loan_remaining || 0)} remaining
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Interest Rate</p>
              <p className="text-2xl font-bold">2% /mo</p>
              <p className="text-xs text-muted-foreground mt-1">Reducing balance</p>
            </CardContent>
          </Card>
        </div>

        {/* Eligibility Requirements */}
        {!eligibility?.eligible && eligibility?.reasons?.length > 0 && (
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="p-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-400">Requirements to be eligible for a loan:</p>
                  <ul className="text-sm text-muted-foreground mt-2 space-y-1">
                    {eligibility.reasons.map((reason, i) => (
                      <li key={i}>• {reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Active Loan Card with Repayment */}
        {activeLoan && activeLoan.status !== 'pending' && (
          <Card className="border-primary/30 bg-primary/5">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                  Active Loan
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge className={getStatusColor(activeLoan.status)}>
                    {activeLoan.status}
                  </Badge>
                  <Button 
                    size="sm" 
                    onClick={() => openRepaymentDialog(activeLoan)}
                    data-testid="make-repayment-btn"
                  >
                    <Banknote className="mr-2 h-4 w-4" />
                    Make Repayment
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-muted-foreground">Principal Amount</p>
                  <p className="text-xl font-bold currency">{formatCurrency(activeLoan.amount)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Monthly Payment</p>
                  <p className="text-xl font-bold currency">{formatCurrency(activeLoan.monthly_payment)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Repaid</p>
                  <p className="text-xl font-bold currency">{formatCurrency(activeLoan.total_repaid || 0)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Remaining</p>
                  <p className="text-xl font-bold currency">
                    {formatCurrency(activeLoan.total_repayment - (activeLoan.total_repaid || 0))}
                  </p>
                </div>
              </div>
              
              {/* Repayment Progress */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Repayment Progress</span>
                  <span>{Math.round(((activeLoan.total_repaid || 0) / activeLoan.total_repayment) * 100)}%</span>
                </div>
                <Progress 
                  value={((activeLoan.total_repaid || 0) / activeLoan.total_repayment) * 100} 
                  className="h-2"
                />
              </div>

              {/* Repayment History */}
              {activeLoan.repayments && activeLoan.repayments.length > 0 && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-sm font-medium mb-2">Recent Repayments</p>
                  <div className="space-y-2">
                    {activeLoan.repayments.slice(0, 3).map((repayment) => (
                      <div key={repayment.id} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{formatDate(repayment.payment_date)}</span>
                        <span className="font-medium currency">{formatCurrency(repayment.amount)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Repayment Dialog */}
        <Dialog open={repaymentDialogOpen} onOpenChange={setRepaymentDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                Make Repayment
              </DialogTitle>
              <DialogDescription>
                Record a loan repayment. Outstanding: {formatCurrency(selectedLoan ? selectedLoan.total_repayment - (selectedLoan.total_repaid || 0) : 0)}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleRepayment} className="space-y-4">
              <div className="form-group">
                <Label htmlFor="repayment-amount">Amount (₦)</Label>
                <Input
                  id="repayment-amount"
                  type="number"
                  min="100"
                  step="100"
                  placeholder="5000"
                  value={repaymentData.amount}
                  onChange={(e) => setRepaymentData(prev => ({ ...prev, amount: e.target.value }))}
                  required
                  className="h-11"
                  data-testid="repayment-amount-input"
                />
              </div>
              <div className="form-group">
                <Label htmlFor="repayment-notes">Notes (Optional)</Label>
                <Textarea
                  id="repayment-notes"
                  placeholder="Payment reference, etc."
                  value={repaymentData.notes}
                  onChange={(e) => setRepaymentData(prev => ({ ...prev, notes: e.target.value }))}
                  rows={2}
                  data-testid="repayment-notes-input"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={submitting}
                data-testid="submit-repayment-btn"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Recording...
                  </>
                ) : (
                  'Record Repayment'
                )}
              </Button>
            </form>
          </DialogContent>
        </Dialog>

        {/* Loans History Table */}
        <Card>
          <CardHeader>
            <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Loan History
            </CardTitle>
            <CardDescription>
              All your loan applications and their status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loans.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Duration</th>
                      <th>Monthly</th>
                      <th>Repaid</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loans.map((loan) => (
                      <tr key={loan.id}>
                        <td>{formatDate(loan.created_at)}</td>
                        <td className="currency font-medium">{formatCurrency(loan.amount)}</td>
                        <td>{loan.duration_months} months</td>
                        <td className="currency">{formatCurrency(loan.monthly_payment)}</td>
                        <td className="currency">{formatCurrency(loan.total_repaid || 0)}</td>
                        <td>
                          <Badge className={getStatusColor(loan.status)}>
                            {loan.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <CreditCard className="empty-state-icon" />
                <p className="empty-state-title">No loan history</p>
                <p className="empty-state-description">
                  Apply for your first loan when you're ready
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Loans;
