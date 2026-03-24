import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';
import { BadgeDollarSign, Loader2, Check, X } from 'lucide-react';

const AdminLoans = () => {
  const { api } = useAuth();
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');

  const fetchLoans = async () => {
    try {
      const response = await api.get('/admin/loans');
      setLoans(response.data);
    } catch (error) {
      console.error('Failed to fetch loans:', error);
      toast.error('Failed to load loans');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoans();
  }, [api]);

  const handleAction = async (loanId, action) => {
    setProcessing(loanId);
    try {
      await api.patch(`/admin/loans/${loanId}/${action}`);
      toast.success(`Loan ${action}d successfully`);
      fetchLoans();
    } catch (error) {
      toast.error(`Failed to ${action} loan`);
    } finally {
      setProcessing(null);
    }
  };

  const filteredLoans = loans.filter(l => {
    const status = (l.status || '').toUpperCase();
    if (activeTab === 'pending') return status === 'PENDING';
    if (activeTab === 'active') return ['APPROVED', 'ACTIVE'].includes(status);
    if (activeTab === 'completed') return ['COMPLETED', 'REJECTED'].includes(status);
    return true;
  });

  const pendingCount = loans.filter(l => (l.status || '').toUpperCase() === 'PENDING').length;
  const totalDisbursed = loans.filter(l => ['APPROVED', 'ACTIVE', 'COMPLETED'].includes((l.status || '').toUpperCase()))
    .reduce((sum, l) => sum + l.amount, 0);

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
      <div className="space-y-6" data-testid="admin-loans-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Loans Management
          </h1>
          <p className="text-muted-foreground">
            Review and approve loan applications
          </p>
        </div>

        {/* Stats */}
        <div className="grid sm:grid-cols-3 gap-4">
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Total Disbursed</p>
              <p className="text-2xl font-bold currency">{formatCurrency(totalDisbursed)}</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Pending Applications</p>
              <p className="text-2xl font-bold">{pendingCount}</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Active Loans</p>
              <p className="text-2xl font-bold">
                {loans.filter(l => ['approved', 'active'].includes(l.status)).length}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Loans Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <BadgeDollarSign className="h-5 w-5" />
              All Loan Applications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="mb-4">
                <TabsTrigger value="pending" className="relative">
                  Pending
                  {pendingCount > 0 && (
                    <span className="ml-2 px-1.5 py-0.5 text-xs bg-destructive text-destructive-foreground rounded-full">
                      {pendingCount}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="active">Active</TabsTrigger>
                <TabsTrigger value="completed">Completed/Rejected</TabsTrigger>
                <TabsTrigger value="all">All</TabsTrigger>
              </TabsList>

              <TabsContent value={activeTab}>
                {filteredLoans.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Member</th>
                          <th>Amount</th>
                          <th>Duration</th>
                          <th>Guarantor</th>
                          <th>Status</th>
                          {activeTab === 'pending' && <th>Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredLoans.map((loan) => (
                          <tr key={loan.id}>
                            <td>{formatDate(loan.created_at)}</td>
                            <td>
                              <div>
                                <p className="font-medium">{loan.user_name}</p>
                                <p className="text-xs text-muted-foreground">{loan.purpose}</p>
                              </div>
                            </td>
                            <td>
                              <div>
                                <p className="currency font-medium">{formatCurrency(loan.amount)}</p>
                                <p className="text-xs text-muted-foreground">{formatCurrency(loan.monthly_payment)}/mo</p>
                              </div>
                            </td>
                            <td>{loan.duration_months} months</td>
                            <td>
                              {loan.guarantor_name ? (
                                <div>
                                  <p className="font-medium">{loan.guarantor_name}</p>
                                  <Badge className="bg-green-500/20 text-green-400 text-xs">Validated</Badge>
                                </div>
                              ) : (
                                <span className="text-muted-foreground">-</span>
                              )}
                            </td>
                            <td>
                              <Badge className={getStatusColor(loan.status)}>
                                {loan.status}
                              </Badge>
                              {loan.days_overdue > 0 && (
                                <Badge className="ml-1 bg-red-500/20 text-red-400 text-xs">
                                  {loan.days_overdue}d overdue
                                </Badge>
                              )}
                            </td>
                            {activeTab === 'pending' && (
                              <td>
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => handleAction(loan.id, 'approve')}
                                    disabled={processing === loan.id}
                                    data-testid={`approve-loan-${loan.id}`}
                                  >
                                    {processing === loan.id ? (
                                      <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                      <>
                                        <Check className="h-4 w-4 mr-1" />
                                        Approve
                                      </>
                                    )}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => handleAction(loan.id, 'reject')}
                                    disabled={processing === loan.id}
                                    data-testid={`reject-loan-${loan.id}`}
                                  >
                                    <X className="h-4 w-4 mr-1" />
                                    Reject
                                  </Button>
                                </div>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state py-12">
                    <BadgeDollarSign className="empty-state-icon" />
                    <p className="empty-state-title">No {activeTab} loans</p>
                    <p className="empty-state-description">
                      {activeTab === 'pending' 
                        ? 'All loan applications have been reviewed' 
                        : 'No loans in this category'}
                    </p>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AdminLoans;
