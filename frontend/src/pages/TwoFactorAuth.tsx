// src/pages/TwoFactorAuth.tsx
import React from 'react';
import { Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const TwoFactorAuth: React.FC = () => {
  const navigate = useNavigate();

  const handleConfirm = () => {
    console.log('2FA Enabled!');
    navigate('/cabinet'); // Redirect back to personal cabinet after 2FA setup
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Two-Factor Authentication Setup</h2>
      <p>
        To enhance your account's security, you can enable Two-Factor Authentication (2FA). After setting it up, you
        will be required to provide a 2FA code when logging in.
      </p>
      <Button type="primary" onClick={handleConfirm}>
        Confirm Setup
      </Button>
    </div>
  );
};

export default TwoFactorAuth;
