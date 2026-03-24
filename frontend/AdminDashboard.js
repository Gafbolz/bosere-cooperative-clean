import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { formatCurrency } from '../../lib/utils';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Users, Wallet, CreditCard, AlertCircle } from 'lucide-react';

const AdminDashboard = () => {
  const { api } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await api.get('/admin/stats');
        setStats(response.data);
      } catch (error) {
        console.error('Failed to fetch admin stats:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [api]);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-64">
          <div className="spinner text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  const memberData = [
    { name: 'Approved', value: stats?.approved_members || 0, color: 'hsl(160, 84%, 39%)' },
    { name: 'Pending', value: stats?.pending_members || 0, color: 'hsl(45, 93%, 58%)' }
  ];

  const statCards = [
    {
      title: 'Total Members',
      value: stats?.total_members || 0,
      subtitle: `${stats?.pending_members || 0} pending approval`,
      icon: Users,
      color: 'text-primary'
    },
    {
      title: 'Total Contributions',
      value: formatCurrency(stats?.total_contributions || 0),
      subtitle: `${stats?.pending_contributions_count || 0} pending`,
      icon: Wallet,
      color: 'text-accent'
    },
    {
      title: 'Loans Disbursed',
      value: formatCurrency(stats?.total_loans_disbursed || 0),
      subtitle: `${stats?.active_loans_count || 0} active loans`,
      icon: CreditCard,
      color: 'text-secondary'
    },
    {
      title: 'Pending Actions',
      value: (stats?.pending_members || 0) + (stats?.pending_contributions_count || 0) + (stats?.pending_loans_count || 0),
      subtitle: 'Members, contributions, loans',
      icon: AlertCircle,
      color: 'text-destructive'
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="admin-dashboard">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Admin Dashboard
          </h1>
          <p className="text-muted-foreground">
            Overview of cooperative activities and pending actions
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {statCards.map((stat, index) => (
            <Card key={index} className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
                    <p className="stat-value">{stat.value}</p>
                    <p className="text-xs text-muted-foreground mt-1">{stat.subtitle}</p>
                  </div>
                  <div className={`w-10 h-10 rounded-lg bg-muted flex items-center justify-center ${stat.color}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Charts */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Members Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                Member Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={memberData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {memberData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value, name) => [value, name]}
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        borderColor: 'hsl(var(--border))',
                        borderRadius: '8px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-center gap-6 mt-4">
                {memberData.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-sm text-muted-foreground">{item.name}: {item.value}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                Pending Actions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Users className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                      <span className="font-medium">Pending Member Approvals</span>
                    </div>
                    <span className="text-2xl font-bold">{stats?.pending_members || 0}</span>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Wallet className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                      <span className="font-medium">Pending Contributions</span>
                    </div>
                    <span className="text-2xl font-bold">{stats?.pending_contributions_count || 0}</span>
                  </div>
                </div>
                
                <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <CreditCard className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                      <span className="font-medium">Pending Loan Applications</span>
                    </div>
                    <span className="text-2xl font-bold">{stats?.pending_loans_count || 0}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AdminDashboard;
