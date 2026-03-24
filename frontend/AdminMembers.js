import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { formatDate } from '../../lib/utils';
import { toast } from 'sonner';
import { Users, UserCheck, Loader2, Shield, CheckCircle, XCircle, Clock } from 'lucide-react';

const AdminMembers = () => {
  const { api } = useAuth();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(null);
  const [verifyingKyc, setVerifyingKyc] = useState(null);

  const fetchMembers = async () => {
    try {
      const response = await api.get('/admin/users');
      setMembers(response.data);
    } catch (error) {
      console.error('Failed to fetch members:', error);
      toast.error('Failed to load members');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [api]);

  const approveMember = async (userId) => {
    setApproving(userId);
    try {
      await api.patch(`/admin/users/${userId}/approve`);
      toast.success('Member approved successfully');
      fetchMembers();
    } catch (error) {
      toast.error('Failed to approve member');
    } finally {
      setApproving(null);
    }
  };

  const verifyKyc = async (userId, status) => {
    setVerifyingKyc(userId);
    try {
      await api.patch(`/admin/users/${userId}/kyc?status=${status}`);
      toast.success(`KYC ${status} successfully`);
      fetchMembers();
    } catch (error) {
      toast.error('Failed to update KYC status');
    } finally {
      setVerifyingKyc(null);
    }
  };

  const getKycBadge = (status) => {
    switch (status) {
      case 'verified':
        return <Badge className="bg-green-500/20 text-green-400"><CheckCircle className="w-3 h-3 mr-1" />Verified</Badge>;
      case 'rejected':
        return <Badge className="bg-red-500/20 text-red-400"><XCircle className="w-3 h-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge className="bg-yellow-500/20 text-yellow-400"><Clock className="w-3 h-3 mr-1" />Pending</Badge>;
    }
  };

  const pendingMembers = members.filter(m => !m.is_approved);
  const approvedMembers = members.filter(m => m.is_approved);

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
      <div className="space-y-6" data-testid="admin-members-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Members Management
          </h1>
          <p className="text-muted-foreground">
            Approve and manage cooperative members
          </p>
        </div>

        {/* Pending Approvals */}
        {pendingMembers.length > 0 && (
          <Card className="border-yellow-200 dark:border-yellow-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-yellow-800 dark:text-yellow-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
                <UserCheck className="h-5 w-5" />
                Pending Approvals ({pendingMembers.length})
              </CardTitle>
              <CardDescription>
                Members waiting for account approval
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Phone</th>
                      <th>Joined</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pendingMembers.map((member) => (
                      <tr key={member.id}>
                        <td className="font-medium">{member.full_name}</td>
                        <td>{member.email}</td>
                        <td>{member.phone}</td>
                        <td>{formatDate(member.created_at)}</td>
                        <td>
                          <Button
                            size="sm"
                            onClick={() => approveMember(member.id)}
                            disabled={approving === member.id}
                            data-testid={`approve-member-${member.id}`}
                          >
                            {approving === member.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              'Approve'
                            )}
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* All Members */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              <Users className="h-5 w-5" />
              All Members ({members.length})
            </CardTitle>
            <CardDescription>
              Complete list of cooperative members with KYC status
            </CardDescription>
          </CardHeader>
          <CardContent>
            {members.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Business</th>
                      <th>KYC Status</th>
                      <th>Member Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((member) => (
                      <tr key={member.id}>
                        <td>
                          <div>
                            <p className="font-medium">{member.full_name}</p>
                            <p className="text-xs text-muted-foreground">{member.phone}</p>
                          </div>
                        </td>
                        <td>{member.email}</td>
                        <td>
                          <div>
                            <p className="font-medium">{member.business_name || '-'}</p>
                            <p className="text-xs text-muted-foreground">
                              {member.cac_registration_number || 'No CAC'}
                            </p>
                          </div>
                        </td>
                        <td>{getKycBadge(member.kyc_status)}</td>
                        <td>
                          <Badge className={member.is_approved ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}>
                            {member.is_approved ? 'Active' : 'Pending'}
                          </Badge>
                        </td>
                        <td>
                          <div className="flex gap-2">
                            {!member.is_approved && (
                              <Button
                                size="sm"
                                onClick={() => approveMember(member.id)}
                                disabled={approving === member.id}
                              >
                                {approving === member.id ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Approve'}
                              </Button>
                            )}
                            {member.kyc_status === 'pending' && member.business_name && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => verifyKyc(member.id, 'verified')}
                                  disabled={verifyingKyc === member.id}
                                >
                                  Verify KYC
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => verifyKyc(member.id, 'rejected')}
                                  disabled={verifyingKyc === member.id}
                                >
                                  Reject
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-12">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No members found</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default AdminMembers;
