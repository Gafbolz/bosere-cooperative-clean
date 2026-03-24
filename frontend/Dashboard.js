import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { formatCurrency, formatDate, getStatusColor } from '../../lib/utils';
import { Link } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { 
  Wallet, 
  TrendingUp, 
  CreditCard, 
  PieChart,
  ArrowRight,
  AlertCircle,
  Plus,
  Calendar,
  Lock,
  CheckCircle,
  XCircle
} from 'lucide-react';

const Dashboard = () => {
  const { api, user } = useAuth();
  const [stats, setStats] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [contributions, setContributions] = useState([]);
  const [eligibility, setEligibility] = useState(null);
  const [nextMeeting, setNextMeeting] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, chartRes, contribRes, eligibilityRes, meetingRes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/dashboard/chart-data'),
          api.get('/contributions'),
          api.get('/eligibility').catch(() => ({ data: null })),
          api.get('/meetings/next').catch(() => ({ data: null }))
        ]);
        setStats(statsRes.data);
        setChartData(chartRes.data.contributions || []);
        setContributions(contribRes.data.slice(0, 5));
        setEligibility(eligibilityRes.data);
        setNextMeeting(meetingRes.data);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
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

  const statCards = [
    {
      title: 'Total Contributions',
      value: formatCurrency(stats?.confirmed_contributions || 0),
      subtitle: `${formatCurrency(stats?.pending_contributions || 0)} pending`,
      icon: Wallet,
      color: 'text-accent'
    },
    {
      title: 'Shares Owned',
      value: `${stats?.total_units?.toFixed(2) || 0} Units`,
      subtitle: `@ ${formatCurrency(stats?.unit_value || 10000)}/unit`,
      icon: PieChart,
      color: 'text-secondary'
    },
    {
      title: 'Loan Eligibility',
      value: formatCurrency(stats?.loan_eligibility || 0),
      subtitle: '3x confirmed contributions',
      icon: TrendingUp,
      color: 'text-primary'
    },
    {
      title: 'Active Loan',
      value: formatCurrency(stats?.active_loan_amount || 0),
      subtitle: stats?.active_loan_amount > 0 
        ? `${formatCurrency(stats?.active_loan_remaining || 0)} remaining`
        : 'No active loan',
      icon: CreditCard,
      color: 'text-chart-4'
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="member-dashboard">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Welcome, {user?.full_name?.split(' ')[0]}!
            </h1>
            <p className="text-muted-foreground">
              Here's your cooperative account overview
            </p>
          </div>
          <Button asChild data-testid="new-contribution-btn">
            <Link to="/dashboard/contributions">
              <Plus className="mr-2 h-4 w-4" />
              New Contribution
            </Link>
          </Button>
        </div>

        {/* Pending Approval Notice */}
        {!user?.is_approved && (
          <Card className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
            <CardContent className="p-4 flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
              <div>
                <p className="font-medium text-yellow-800 dark:text-yellow-200">Account Pending Approval</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  Your membership is awaiting admin approval. You'll be notified once approved.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 stagger-children">
          {statCards.map((stat, index) => (
            <Card key={index} className="stat-card">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
                    <p className="stat-value currency">{stat.value}</p>
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

        {/* Eligibility & Meeting Info */}
        <div className="grid md:grid-cols-2 gap-4">
          {/* Loan Eligibility Card */}
          <Card className="border-primary/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                {eligibility?.eligible ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                Loan Eligibility Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge className={eligibility?.eligible ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}>
                  {eligibility?.eligible ? 'Eligible' : 'Not Eligible'}
                </Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Loan Limit</span>
                <span className="font-semibold">{formatCurrency(eligibility?.loan_limit || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Tier</span>
                <span className="font-semibold">{eligibility?.multiplier || 0}x Savings</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground flex items-center gap-1">
                  <Lock className="w-3 h-3" /> Locked Collateral
                </span>
                <span className="font-semibold">{formatCurrency(stats?.locked_collateral || 0)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Available Savings</span>
                <span className="font-semibold text-green-500">
                  {formatCurrency((stats?.confirmed_contributions || 0) - (stats?.locked_collateral || 0))}
                </span>
              </div>
              {eligibility?.reasons?.length > 0 && (
                <div className="mt-3 p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs font-medium mb-2">Requirements needed:</p>
                  <ul className="text-xs text-muted-foreground space-y-1">
                    {eligibility.reasons.map((reason, i) => (
                      <li key={i} className="flex items-start gap-1">
                        <span className="text-red-400">•</span> {reason}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Next Meeting Card */}
          <Card className="border-secondary/20">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="w-5 h-5 text-secondary" />
                Next Cooperative Meeting
              </CardTitle>
            </CardHeader>
            <CardContent>
              {nextMeeting ? (
                <div className="space-y-3">
                  <div className="p-4 bg-secondary/10 rounded-lg text-center">
                    <p className="text-2xl font-bold">{new Date(nextMeeting.meeting_date).toLocaleDateString('en-US', { weekday: 'long' })}</p>
                    <p className="text-lg">{new Date(nextMeeting.meeting_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
                    <p className="text-sm text-muted-foreground mt-1">{nextMeeting.meeting_time}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium">{nextMeeting.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      All members are expected to attend monthly meetings for loan discussions, contributions, and cooperative updates.
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">No upcoming meetings scheduled</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Chart and Recent Activity */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Contributions Chart */}
          <Card className="lg:col-span-2 chart-container">
            <CardHeader>
              <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                Contribution History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(160, 84%, 39%)" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="hsl(160, 84%, 39%)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                      <XAxis 
                        dataKey="month" 
                        className="text-xs fill-muted-foreground"
                        tickFormatter={(value) => value.slice(5)}
                      />
                      <YAxis 
                        className="text-xs fill-muted-foreground"
                        tickFormatter={(value) => `₦${(value/1000).toFixed(0)}k`}
                      />
                      <Tooltip 
                        formatter={(value) => [formatCurrency(value), 'Amount']}
                        labelFormatter={(label) => `Month: ${label}`}
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          borderColor: 'hsl(var(--border))',
                          borderRadius: '8px'
                        }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="amount" 
                        stroke="hsl(160, 84%, 39%)" 
                        fillOpacity={1} 
                        fill="url(#colorAmount)" 
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="empty-state h-[300px]">
                  <Wallet className="empty-state-icon" />
                  <p className="empty-state-title">No contribution data yet</p>
                  <p className="empty-state-description">
                    Start making contributions to see your history chart
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Contributions */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle style={{ fontFamily: 'Manrope, sans-serif' }}>
                Recent Activity
              </CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link to="/dashboard/contributions">
                  View All
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </Button>
            </CardHeader>
            <CardContent>
              {contributions.length > 0 ? (
                <div className="space-y-4">
                  {contributions.map((contribution) => (
                    <div 
                      key={contribution.id} 
                      className="flex items-center justify-between py-2 border-b border-border last:border-0"
                    >
                      <div>
                        <p className="font-medium currency">{formatCurrency(contribution.amount)}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(contribution.created_at)}</p>
                      </div>
                      <Badge className={getStatusColor(contribution.status)}>
                        {contribution.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state py-8">
                  <p className="text-sm text-muted-foreground">No contributions yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="card-hover cursor-pointer" onClick={() => window.location.href = '/dashboard/contributions'}>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
                <Wallet className="h-6 w-6 text-accent" />
              </div>
              <div>
                <h3 className="font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Make Contribution</h3>
                <p className="text-sm text-muted-foreground">Add to your share capital</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="card-hover cursor-pointer" onClick={() => window.location.href = '/dashboard/loans'}>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <CreditCard className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Apply for Loan</h3>
                <p className="text-sm text-muted-foreground">Up to {formatCurrency(stats?.loan_eligibility || 0)}</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="card-hover cursor-pointer" onClick={() => window.location.href = '/dashboard/calculator'}>
            <CardContent className="p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-secondary/20 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-secondary" />
              </div>
              <div>
                <h3 className="font-semibold" style={{ fontFamily: 'Manrope, sans-serif' }}>Loan Calculator</h3>
                <p className="text-sm text-muted-foreground">Estimate your repayments</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
