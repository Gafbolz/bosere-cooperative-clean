-- Bosere Cooperative - Row Level Security (RLS) Policies
-- This script enables RLS and creates policies for all core tables

-- ============================================
-- HELPER: Create a function to get current user's role
-- ============================================

-- Function to check if current user is admin based on JWT claims
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  -- Check if the user has admin role in our users table
  -- This uses the Supabase auth.uid() function
  RETURN EXISTS (
    SELECT 1 FROM public.users 
    WHERE supabase_user_id = auth.uid()::text 
    AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user's ID from our users table
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT id FROM public.users 
    WHERE supabase_user_id = auth.uid()::text
    LIMIT 1
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- USERS TABLE RLS
-- ============================================

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own profile
CREATE POLICY "users_select_own" ON public.users
  FOR SELECT
  USING (
    supabase_user_id = auth.uid()::text
    OR public.is_admin()
  );

-- Policy: Users can update their own non-sensitive fields
CREATE POLICY "users_update_own" ON public.users
  FOR UPDATE
  USING (supabase_user_id = auth.uid()::text)
  WITH CHECK (
    supabase_user_id = auth.uid()::text
    -- Prevent users from changing their own role or approval status
    AND role = (SELECT role FROM public.users WHERE supabase_user_id = auth.uid()::text)
    AND is_approved = (SELECT is_approved FROM public.users WHERE supabase_user_id = auth.uid()::text)
  );

-- Policy: Admins can read all users
CREATE POLICY "users_admin_select" ON public.users
  FOR SELECT
  USING (public.is_admin());

-- Policy: Admins can update all users (including approval)
CREATE POLICY "users_admin_update" ON public.users
  FOR UPDATE
  USING (public.is_admin());

-- Policy: Allow new user creation during registration
CREATE POLICY "users_insert" ON public.users
  FOR INSERT
  WITH CHECK (supabase_user_id = auth.uid()::text);

-- ============================================
-- CONTRIBUTIONS TABLE RLS
-- ============================================

-- Enable RLS
ALTER TABLE public.contributions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own contributions
CREATE POLICY "contributions_select_own" ON public.contributions
  FOR SELECT
  USING (
    user_id = public.current_user_id()
    OR public.is_admin()
  );

-- Policy: Users can create contributions for themselves
CREATE POLICY "contributions_insert_own" ON public.contributions
  FOR INSERT
  WITH CHECK (
    user_id = public.current_user_id()
    AND status = 'pending'  -- New contributions must be pending
  );

-- Policy: Admins can read all contributions
CREATE POLICY "contributions_admin_select" ON public.contributions
  FOR SELECT
  USING (public.is_admin());

-- Policy: Admins can update contributions (for approval)
CREATE POLICY "contributions_admin_update" ON public.contributions
  FOR UPDATE
  USING (public.is_admin());

-- Policy: Admins can delete contributions
CREATE POLICY "contributions_admin_delete" ON public.contributions
  FOR DELETE
  USING (public.is_admin());

-- ============================================
-- LOANS TABLE RLS
-- ============================================

-- Enable RLS
ALTER TABLE public.loans ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own loans
CREATE POLICY "loans_select_own" ON public.loans
  FOR SELECT
  USING (
    user_id = public.current_user_id()
    OR public.is_admin()
  );

-- Policy: Users can create loan applications for themselves
CREATE POLICY "loans_insert_own" ON public.loans
  FOR INSERT
  WITH CHECK (
    user_id = public.current_user_id()
    AND status = 'pending'  -- New loans must be pending
  );

-- Policy: Admins can read all loans
CREATE POLICY "loans_admin_select" ON public.loans
  FOR SELECT
  USING (public.is_admin());

-- Policy: Admins can update loans (for approval/rejection)
CREATE POLICY "loans_admin_update" ON public.loans
  FOR UPDATE
  USING (public.is_admin());

-- Policy: Admins can delete loans
CREATE POLICY "loans_admin_delete" ON public.loans
  FOR DELETE
  USING (public.is_admin());

-- ============================================
-- REPAYMENTS TABLE RLS
-- ============================================

-- Enable RLS
ALTER TABLE public.repayments ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read repayments for their own loans
CREATE POLICY "repayments_select_own" ON public.repayments
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.loans 
      WHERE loans.id = repayments.loan_id 
      AND loans.user_id = public.current_user_id()
    )
    OR public.is_admin()
  );

-- Policy: Users can create repayments for their own active loans
CREATE POLICY "repayments_insert_own" ON public.repayments
  FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.loans 
      WHERE loans.id = loan_id 
      AND loans.user_id = public.current_user_id()
      AND loans.status IN ('approved', 'active')
    )
  );

-- Policy: Admins can read all repayments
CREATE POLICY "repayments_admin_select" ON public.repayments
  FOR SELECT
  USING (public.is_admin());

-- Policy: Admins can manage all repayments
CREATE POLICY "repayments_admin_all" ON public.repayments
  FOR ALL
  USING (public.is_admin());

-- ============================================
-- NOTIFICATIONS TABLE RLS
-- ============================================

-- Enable RLS
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own notifications
CREATE POLICY "notifications_select_own" ON public.notifications
  FOR SELECT
  USING (user_id = public.current_user_id());

-- Policy: Users can update their own notifications (mark as read)
CREATE POLICY "notifications_update_own" ON public.notifications
  FOR UPDATE
  USING (user_id = public.current_user_id());

-- Policy: System/Admin can create notifications for any user
CREATE POLICY "notifications_admin_insert" ON public.notifications
  FOR INSERT
  WITH CHECK (public.is_admin());

-- Policy: Admins can read all notifications
CREATE POLICY "notifications_admin_select" ON public.notifications
  FOR SELECT
  USING (public.is_admin());

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT USAGE ON SCHEMA public TO anon;

-- Grant table permissions to authenticated users
GRANT SELECT, INSERT, UPDATE ON public.users TO authenticated;
GRANT SELECT, INSERT ON public.contributions TO authenticated;
GRANT SELECT, INSERT ON public.loans TO authenticated;
GRANT SELECT, INSERT ON public.repayments TO authenticated;
GRANT SELECT, UPDATE ON public.notifications TO authenticated;

-- Grant function execution
GRANT EXECUTE ON FUNCTION public.is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION public.current_user_id() TO authenticated;

-- ============================================
-- VERIFICATION QUERIES (for testing)
-- ============================================

-- To verify RLS is enabled:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- To list all policies:
-- SELECT tablename, policyname, cmd, qual FROM pg_policies WHERE schemaname = 'public';
