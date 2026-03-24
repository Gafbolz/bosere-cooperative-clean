import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog';
import { formatCurrency, formatDate, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';
import { Plus, Wallet, Loader2 } from 'lucide-react';

const Contributions = () => {
  const { api, user } = useAuth();
  const [contributions, setContributions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    amount: '',
    description: ''
  });

  const fetchContributions = async () => {
    try {
      const response = await api.get('/contributions');
      setContributions(response.data);
    } catch (error) {
      console.error('Failed to fetch contributions:', error);
      toast.error('Failed to load contributions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContributions();
  }, [api]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!user?.is_approved) {
      toast.error('Your account must be approved to make contributions');
      return;
    }

    const amount = parseFloat(formData.amount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    setSubmitting(true);
    try {
      await api.post('/contributions', {
        amount,
        description: formData.description
      });
      toast.success('Contribution submitted for approval');
      setDialogOpen(false);
      setFormData({ amount: '', description: '' });
      fetchContributions();
    } catch (error) {
      const message = error.message || 'Failed to submit contribution';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const totalConfirmed = contributions
    .filter(c => (c.status || '').toUpperCase() === 'APPROVED')
    .reduce((sum, c) => sum + c.amount, 0);

  const totalPending = contributions
    .filter(c => (c.status || '').toUpperCase() === 'PENDING')
    .reduce((sum, c) => sum + c.amount, 0);

  const totalUnits = totalConfirmed / 10000;

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
      <div className="space-y-6" data-testid="contributions-page">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Contributions
            </h1>
            <p className="text-muted-foreground">
              Manage your share capital contributions
            </p>
          </div>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button data-testid="add-contribution-btn">
                <Plus className="mr-2 h-4 w-4" />
                Add Contribution
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                  New Contribution
                </DialogTitle>
                <DialogDescription>
                  Make a new contribution to your share capital. ₦10,000 = 1 Unit.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="form-group">
                  <Label htmlFor="amount">Amount (₦)</Label>
                  <Input
                    id="amount"
                    type="number"
                    min="1000"
                    step="1000"
                    placeholder="10000"
                    value={formData.amount}
                    onChange={(e) => setFormData(prev => ({ ...prev, amount: e.target.value }))}
                    required
                    className="h-11"
                    data-testid="contribution-amount-input"
                  />
                  {formData.amount && (
                    <p className="text-sm text-muted-foreground mt-1">
                      = {(parseFloat(formData.amount) / 10000).toFixed(2)} Units
                    </p>
                  )}
                </div>
                <div className="form-group">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Monthly contribution, etc."
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={3}
                    data-testid="contribution-description-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={submitting}
                  data-testid="submit-contribution-btn"
                >
                  {submitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    'Submit Contribution'
                  )}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Summary Cards */}
        <div className="grid sm:grid-cols-3 gap-4">
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Confirmed Contributions</p>
              <p className="text-2xl font-bold currency">{formatCurrency(totalConfirmed)}</p>
              <p className="text-xs text-muted-foreground mt-1">{totalUnits.toFixed(2)} Units</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Pending Approval</p>
              <p className="text-2xl font-bold currency">{formatCurrency(totalPending)}</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Loan Eligibility</p>
              <p className="text-2xl font-bold currency">{formatCurrency(totalConfirmed * 3)}</p>
              <p className="text-xs text-muted-foreground mt-1">3x confirmed contributions</p>
            </CardContent>
          </Card>
        </div>

        {/* Contributions Table */}
        <Card>
          <CardHeader>
            <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
              Contribution History
            </CardTitle>
            <CardDescription>
              All your contributions to the cooperative
            </CardDescription>
          </CardHeader>
          <CardContent>
            {contributions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Units</th>
                      <th>Description</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contributions.map((contribution) => (
                      <tr key={contribution.id}>
                        <td>{formatDate(contribution.created_at)}</td>
                        <td className="currency font-medium">{formatCurrency(contribution.amount)}</td>
                        <td>{(contribution.amount / 10000).toFixed(2)}</td>
                        <td className="text-muted-foreground">
                          {contribution.description || '-'}
                        </td>
                        <td>
                          <Badge className={getStatusColor(contribution.status)}>
                            {contribution.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <Wallet className="empty-state-icon" />
                <p className="empty-state-title">No contributions yet</p>
                <p className="empty-state-description">
                  Start building your share capital by making your first contribution
                </p>
                <Button 
                  className="mt-4" 
                  onClick={() => setDialogOpen(true)}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Make First Contribution
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Contributions;
