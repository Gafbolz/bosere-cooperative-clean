import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { DashboardLayout } from '../../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { toast } from 'sonner';
import { 
  User, Building2, FileText, Upload, Loader2, CheckCircle, XCircle, Clock,
  CreditCard, Shield, AlertTriangle
} from 'lucide-react';

const Profile = () => {
  const { api, user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    business_name: '',
    residential_address: '',
    business_address: '',
    business_type: '',
    years_in_operation: '',
    cac_registration_number: '',
    cac_certificate_url: '',
    government_id_url: ''
  });

  useEffect(() => {
    fetchProfile();
  }, [api]);

  const fetchProfile = async () => {
    try {
      const response = await api.get('/profile/enhanced');
      setProfile(response.data);
      setFormData({
        full_name: response.data.full_name || '',
        phone: response.data.phone || '',
        business_name: response.data.business_name || '',
        residential_address: response.data.residential_address || '',
        business_address: response.data.business_address || '',
        business_type: response.data.business_type || '',
        years_in_operation: response.data.years_in_operation || '',
        cac_registration_number: response.data.cac_registration_number || '',
        cac_certificate_url: response.data.cac_certificate_url || '',
        government_id_url: response.data.government_id_url || ''
      });
    } catch (error) {
      console.error('Failed to fetch profile:', error);
      toast.error('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await api.put('/profile/kyc', {
        business_name: formData.business_name,
        residential_address: formData.residential_address,
        business_address: formData.business_address,
        business_type: formData.business_type,
        years_in_operation: formData.years_in_operation ? parseInt(formData.years_in_operation) : null,
        cac_registration_number: formData.cac_registration_number,
        cac_certificate_url: formData.cac_certificate_url,
        government_id_url: formData.government_id_url
      });
      
      toast.success('Profile updated successfully. KYC is now pending verification.');
      fetchProfile();
    } catch (error) {
      toast.error(error.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const getKYCStatusBadge = (status) => {
    switch (status) {
      case 'verified':
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/30"><CheckCircle className="w-3 h-3 mr-1" /> Verified</Badge>;
      case 'rejected':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30"><XCircle className="w-3 h-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
    }
  };

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
      <div className="space-y-6" data-testid="profile-page">
        {/* Header */}
        <div>
          <h1 className="text-2xl md:text-3xl font-bold" style={{ fontFamily: 'Manrope, sans-serif' }}>
            My Profile & KYC
          </h1>
          <p className="text-muted-foreground">
            Manage your profile and CAC/KYC verification
          </p>
        </div>

        {/* Status Cards */}
        <div className="grid sm:grid-cols-3 gap-4">
          <Card className="stat-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">KYC Status</p>
                  <div className="mt-1">{getKYCStatusBadge(profile?.kyc_status)}</div>
                </div>
                <Shield className="w-8 h-8 text-muted-foreground/50" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="stat-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Credit Score</p>
                  <p className="text-2xl font-bold">{profile?.credit_score || 50}/100</p>
                </div>
                <CreditCard className="w-8 h-8 text-muted-foreground/50" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="stat-card">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Membership</p>
                  <p className="text-2xl font-bold">{profile?.membership_months || 0} months</p>
                </div>
                <User className="w-8 h-8 text-muted-foreground/50" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* KYC Warning */}
        {profile?.kyc_status !== 'verified' && (
          <Card className="border-yellow-500/30 bg-yellow-500/5">
            <CardContent className="p-4">
              <div className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-yellow-400">KYC Verification Required</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Complete your CAC/KYC verification to access loan features and increase your eligibility tier.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Profile Form */}
        <form onSubmit={handleSubmit}>
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Personal Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Personal Information
                </CardTitle>
                <CardDescription>Your basic personal details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    disabled
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    value={profile?.email || ''}
                    disabled
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <Input
                    id="phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    disabled
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="residential_address">Residential Address</Label>
                  <Textarea
                    id="residential_address"
                    value={formData.residential_address}
                    onChange={(e) => setFormData({ ...formData, residential_address: e.target.value })}
                    placeholder="Enter your home address"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Business Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="w-5 h-5" />
                  Business Information
                </CardTitle>
                <CardDescription>Your business details for CAC verification</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="business_name">Business Name</Label>
                  <Input
                    id="business_name"
                    value={formData.business_name}
                    onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                    placeholder="Enter your business name"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="business_type">Business Type</Label>
                  <Select
                    value={formData.business_type}
                    onValueChange={(value) => setFormData({ ...formData, business_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select business type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="trading">Trading/Retail</SelectItem>
                      <SelectItem value="services">Services</SelectItem>
                      <SelectItem value="manufacturing">Manufacturing</SelectItem>
                      <SelectItem value="agriculture">Agriculture</SelectItem>
                      <SelectItem value="technology">Technology</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="years_in_operation">Years in Operation</Label>
                  <Input
                    id="years_in_operation"
                    type="number"
                    min="0"
                    value={formData.years_in_operation}
                    onChange={(e) => setFormData({ ...formData, years_in_operation: e.target.value })}
                    placeholder="e.g., 5"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="business_address">Business Address</Label>
                  <Textarea
                    id="business_address"
                    value={formData.business_address}
                    onChange={(e) => setFormData({ ...formData, business_address: e.target.value })}
                    placeholder="Enter your business address"
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            {/* CAC Documents */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  CAC Documents
                </CardTitle>
                <CardDescription>Upload your CAC registration documents</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cac_registration_number">CAC Registration Number</Label>
                    <Input
                      id="cac_registration_number"
                      value={formData.cac_registration_number}
                      onChange={(e) => setFormData({ ...formData, cac_registration_number: e.target.value })}
                      placeholder="e.g., RC-1234567"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="cac_certificate_url">CAC Certificate URL</Label>
                    <Input
                      id="cac_certificate_url"
                      value={formData.cac_certificate_url}
                      onChange={(e) => setFormData({ ...formData, cac_certificate_url: e.target.value })}
                      placeholder="Link to uploaded CAC certificate"
                    />
                    <p className="text-xs text-muted-foreground">
                      Upload your CAC certificate to a cloud storage and paste the link here
                    </p>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="government_id_url">Government ID URL</Label>
                  <Input
                    id="government_id_url"
                    value={formData.government_id_url}
                    onChange={(e) => setFormData({ ...formData, government_id_url: e.target.value })}
                    placeholder="Link to uploaded government ID (NIN, Voter's Card, etc.)"
                  />
                  <p className="text-xs text-muted-foreground">
                    Upload a valid government-issued ID to a cloud storage and paste the link here
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Submit Button */}
          <div className="mt-6 flex justify-end">
            <Button type="submit" disabled={saving} size="lg">
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Submit for KYC Review
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  );
};

export default Profile;
