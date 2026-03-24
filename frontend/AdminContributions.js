import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { formatCurrency, formatDate, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';
import { FileCheck, Loader2, Check, X } from 'lucide-react';

const AdminContributions = () => {
  const { api } = useAuth();
  const [contributions, setContributions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [activeTab, setActiveTab] = useState('pending');

  const fetchContributions = async () => {
    try {
      const response = await api.get('/admin/contributions');
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

  const handleAction = async (contributionId, action) => {
    console.log(`[Admin] handleAction called: ${action} for ${contributionId}`);
    setProcessing(contributionId);
    try {
      console.log(`[Admin] Making PATCH request to /admin/contributions/${contributionId}/${action}`);
      const response = await api.patch(`/admin/contributions/${contributionId}/${action}`);
      console.log(`[Admin] ${action} response:`, response);
      toast.success(`Contribution ${action}d successfully`);
      fetchContributions();
    } catch (error) {
      console.error(`[Admin] ${action} error:`, error);
      const errorMessage = error.message || `Failed to ${action} contribution`;
      toast.error(errorMessage);
    } finally {
      setProcessing(null);
    }
  };

  const filteredContributions = contributions.filter(c => {
    const status = (c.status || '').toUpperCase();
    if (activeTab === 'pending') return status === 'PENDING';
    if (activeTab === 'approved') return status === 'APPROVED';
    if (activeTab === 'rejected') return status === 'REJECTED';
    return true;
  });

  const pendingCount = contributions.filter(c => (c.status || '').toUpperCase() === 'PENDING').length;

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
      <div className="space-y-6" data-testid="admin-contributions-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Contributions Management
          </h1>
          <p className="text-muted-foreground">
            Review and approve member contributions
          </p>
        </div>

        {/* Stats */}
        <div className="grid sm:grid-cols-3 gap-4">
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Total Contributions</p>
              <p className="text-2xl font-bold currency">
                {formatCurrency(contributions.filter(c => (c.status || '').toUpperCase() === 'APPROVED').reduce((sum, c) => sum + c.amount, 0))}
              </p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Pending Approval</p>
              <p className="text-2xl font-bold">{pendingCount}</p>
            </CardContent>
          </Card>
          <Card className="stat-card">
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground mb-1">Total Records</p>
              <p className="text-2xl font-bold">{contributions.length}</p>
            </CardContent>
          </Card>
        </div>

        {/* Contributions Table */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <FileCheck className="h-5 w-5" />
              All Contributions
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
                <TabsTrigger value="approved">Approved</TabsTrigger>
                <TabsTrigger value="rejected">Rejected</TabsTrigger>
                <TabsTrigger value="all">All</TabsTrigger>
              </TabsList>

              <TabsContent value={activeTab}>
                {filteredContributions.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Member</th>
                          <th>Amount</th>
                          <th>Description</th>
                          <th>Status</th>
                          {activeTab === 'pending' && <th>Actions</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredContributions.map((contribution) => (
                          <tr key={contribution.id}>
                            <td>{formatDate(contribution.created_at)}</td>
                            <td className="font-medium">{contribution.user_name}</td>
                            <td className="currency font-medium">{formatCurrency(contribution.amount)}</td>
                            <td className="text-muted-foreground max-w-[200px] truncate">
                              {contribution.description || '-'}
                            </td>
                            <td>
                              <Badge className={getStatusColor(contribution.status)}>
                                {contribution.status}
                              </Badge>
                            </td>
                            {activeTab === 'pending' && (
                              <td>
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      e.preventDefault();
                                      handleAction(contribution.id, 'approve');
                                    }}
                                    disabled={processing === contribution.id}
                                    data-testid={`approve-contribution-${contribution.id}`}
                                  >
                                    {processing === contribution.id ? (
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
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      e.preventDefault();
                                      handleAction(contribution.id, 'reject');
                                    }}
                                    disabled={processing === contribution.id}
                                    data-testid={`reject-contribution-${contribution.id}`}
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
                    <FileCheck className="empty-state-icon" />
                    <p className="empty-state-title">No {activeTab} contributions</p>
                    <p className="empty-state-description">
                      {activeTab === 'pending' 
                        ? 'All contributions have been reviewed' 
                        : 'No contributions in this category'}
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

export default AdminContributions;
