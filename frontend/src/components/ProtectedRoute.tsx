import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Roles, roleWeightMapping } from '../constants/roles';
import { User } from '../context/UserContext';
import message from 'antd/es/message';

const isAuthorized = (userRole: string, requiredRole: Roles): boolean => {
  return roleWeightMapping[requiredRole] <= roleWeightMapping[userRole as Roles];
};

interface ProtectedRouteProps {
  children: React.ReactNode;
  user: User | null;
  requiredRole: Roles;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, user, requiredRole }) => {
  const location = useLocation();

  if (!user || !isAuthorized(user.role, requiredRole)) {
    localStorage.setItem('lastVisitedPage', location.pathname);
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
