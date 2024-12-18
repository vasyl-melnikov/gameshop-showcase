import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

export type User = {
    email: string
    first_name: string
    last_name: string
    role: string
    ukey: string
    username: string
    mfa_enabled: boolean
}
interface UserContextType {
  user: User | null;
  loading: boolean;
  setUser: React.Dispatch<React.SetStateAction<User | null>>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const authToken = localStorage.getItem('authToken');

    if (!authToken) {
      navigate('/login', { replace: true });
      return;
    }

    const validateToken = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/users/me`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`
          },
        });

        if (!response.ok) {
          throw new Error('Token validation failed');
        }

        const userData = await response.json();
        setUser(userData as User);
      } catch (error) {
        console.error('Error validating token:', error);
        localStorage.removeItem('authToken');
        navigate('/login', { replace: true });
      } finally {
        setLoading(false);
      }
    };

    if (authToken) {
      validateToken();
    } else {
      setLoading(false);  // If no authToken, just set loading to false immediately
    }
  }, [navigate]); // Ensure that `useEffect` only depends on navigate

  return (
    <UserContext.Provider value={{ user, loading, setUser }}>
      {children}
    </UserContext.Provider>
  );
};
