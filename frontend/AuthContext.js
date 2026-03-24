import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext(null);

// Get API URL with HTTPS enforcement
const getApiUrl = () => {
  const backendUrl = process.env.REACT_APP_BACKEND_URL;
  
  if (!backendUrl) {
    console.error('[Auth] REACT_APP_BACKEND_URL is not set!');
    return null;
  }
  
  let url = backendUrl.trim();
  
  // Force HTTPS
  if (url.startsWith('http://')) {
    url = url.replace('http://', 'https://');
  }
  
  // Ensure starts with https://
  if (!url.startsWith('https://')) {
    url = 'https://' + url;
  }
  
  // Remove trailing slash
  url = url.replace(/\/+$/, '');
  
  return `${url}/api`;
};

// API helper using native fetch - returns { data } like axios for compatibility
const createApiClient = (accessToken = null) => {
  const baseUrl = getApiUrl();
  
  if (!baseUrl) {
    console.error('[API] No base URL configured');
    // Return a dummy client that throws on use
    const throwNoConfig = () => { throw new Error('API not configured'); };
    return {
      get: throwNoConfig,
      post: throwNoConfig,
      put: throwNoConfig,
      delete: throwNoConfig,
    };
  }
  
  const headers = {
    'Content-Type': 'application/json',
    ...(accessToken && { 'Authorization': `Bearer ${accessToken}` })
  };
  
  const request = async (method, path, data = null) => {
    const url = `${baseUrl}${path}`;
    console.log(`[API] ${method} ${url}`);
    
    const options = {
      method,
      headers,
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    }
    
    let response;
    let responseText;
    let responseData = null;
    
    try {
      response = await fetch(url, options);
      
      // Read response body ONCE as text
      responseText = await response.text();
      
      // Try to parse as JSON
      if (responseText) {
        try {
          responseData = JSON.parse(responseText);
        } catch {
          // Not JSON, keep as null
          console.log(`[API] Response is not JSON: ${responseText.substring(0, 100)}`);
        }
      }
      
      if (!response.ok) {
        // Extract error message from parsed data or use status text
        const errorMessage = responseData?.detail || 
                           (typeof responseData === 'string' ? responseData : null) ||
                           response.statusText || 
                           `HTTP ${response.status}`;
        console.error(`[API] Error ${response.status}: ${errorMessage}`);
        throw new Error(errorMessage);
      }
      
      console.log(`[API] Success ${response.status}`);
      // Return in axios-compatible format
      return { data: responseData, status: response.status };
    } catch (error) {
      // Don't wrap fetch/network errors, just rethrow with clean message
      const message = error.message || 'Request failed';
      console.error(`[API] Request failed: ${message}`);
      throw new Error(message);
    }
  };
  
  return {
    get: (path, config) => request('GET', path),
    post: (path, data) => request('POST', path, data),
    put: (path, data) => request('PUT', path, data),
    patch: (path, data) => request('PATCH', path, data),
    delete: (path) => request('DELETE', path),
  };
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Create API client based on current session
  const api = useMemo(() => {
    return createApiClient(session?.access_token);
  }, [session?.access_token]);

  // Fetch user profile from backend
  const fetchUserProfile = useCallback(async (accessToken) => {
    if (!accessToken) {
      console.log('[Auth] No access token for profile fetch');
      return null;
    }
    
    const apiClient = createApiClient(accessToken);
    
    try {
      console.log('[Auth] Fetching user profile...');
      const response = await apiClient.get('/auth/check-user');
      
      if (response.data?.exists) {
        const userData = response.data.user;
        setUser(userData);
        return userData;
      }
      
      return null;
    } catch (err) {
      console.error('[Auth] Profile fetch error:', err.message);
      return null;
    }
  }, []);

  // Initialize auth state
  useEffect(() => {
    let mounted = true;

    const initAuth = async () => {
      console.log('[Auth] Initializing...');
      
      try {
        const { data, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          console.error('[Auth] Session error:', sessionError.message);
          if (mounted) {
            setError(sessionError.message);
            setLoading(false);
          }
          return;
        }
        
        if (!data?.session) {
          console.log('[Auth] No active session');
          if (mounted) setLoading(false);
          return;
        }
        
        console.log('[Auth] Session found for:', data.session.user.email);
        
        if (mounted) {
          setSession(data.session);
          await fetchUserProfile(data.session.access_token);
          setLoading(false);
        }
      } catch (err) {
        console.error('[Auth] Init error:', err.message);
        if (mounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    };

    initAuth();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        if (!mounted) return;
        
        console.log('[Auth] State changed:', event);
        
        setSession(newSession);
        
        if (newSession) {
          await fetchUserProfile(newSession.access_token);
        } else {
          setUser(null);
        }
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [fetchUserProfile]);

  // Register new user
  const register = async (userData) => {
    console.log('[Auth] Registering:', userData.email);
    setError(null);

    const { email, password, full_name, phone } = userData;
    
    try {
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name, phone }
        }
      });

      if (authError) {
        console.error('[Auth] Signup error:', authError.message);
        throw authError;
      }

      console.log('[Auth] Supabase signup OK');

      if (authData.user && authData.session) {
        const apiClient = createApiClient(authData.session.access_token);
        
        console.log('[Auth] Creating backend profile...');
        const response = await apiClient.post('/auth/register', {
          email,
          full_name,
          phone,
          supabase_user_id: authData.user.id
        });
        
        console.log('[Auth] Profile created:', response.data.id);
        
        setUser(response.data);
        setSession(authData.session);
        return response.data;
      }

      if (authData.user && !authData.session) {
        throw new Error('Please check your email to confirm your account.');
      }

      return null;
    } catch (err) {
      console.error('[Auth] Registration error:', err.message);
      setError(err.message);
      throw err;
    }
  };

  // Login user
  const login = async (email, password) => {
    console.log('[Auth] Logging in:', email);
    setError(null);

    try {
      const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (authError) {
        console.error('[Auth] Login error:', authError.message);
        throw authError;
      }

      console.log('[Auth] Login successful');

      if (authData.session) {
        setSession(authData.session);
        const userProfile = await fetchUserProfile(authData.session.access_token);
        return userProfile;
      }

      return null;
    } catch (err) {
      console.error('[Auth] Login error:', err.message);
      setError(err.message);
      throw err;
    }
  };

  // Logout user
  const logout = async () => {
    console.log('[Auth] Logging out');
    setError(null);
    
    try {
      await supabase.auth.signOut();
      setSession(null);
      setUser(null);
      console.log('[Auth] Logout OK');
    } catch (err) {
      console.error('[Auth] Logout error:', err.message);
      setError(err.message);
    }
  };

  const value = useMemo(() => {
    const isAdmin = user?.role?.toUpperCase() === 'ADMIN';
    
    return {
      user,
      session,
      loading,
      error,
      login,
      register,
      logout,
      api,
      supabase,
      isAuthenticated: !!user,
      isAdmin,
      isApproved: user?.is_approved
    };
  }, [user, session, loading, error, api]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
