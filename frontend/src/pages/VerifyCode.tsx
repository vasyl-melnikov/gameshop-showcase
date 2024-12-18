// src/pages/VerifyCode.tsx
import React from 'react';
import { Form, Input, Button } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';

const VerifyCode: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleVerification = (values: any) => {
    // Mock successful verification
    if (location.state.type === 'password') {
      alert('Password changed successfully!');
    } else if (location.state.type === 'email') {
      alert('Email changed successfully!');
    }
    navigate('/cabinet');
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Verify Your {location.state.type === 'password' ? 'Password' : 'Email'} Change</h2>
      <Form layout="vertical" onFinish={handleVerification}>
        <Form.Item label="Verification Code" required>
          <Input placeholder="Enter code sent to your email" />
        </Form.Item>
        <Button type="primary" htmlType="submit">Verify Code</Button>
      </Form>
    </div>
  );
};

export default VerifyCode;
