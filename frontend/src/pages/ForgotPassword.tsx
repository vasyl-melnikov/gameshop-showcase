// ForgotPassword.tsx
import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { API_BASE_URL } from '../config';

const ForgotPassword: React.FC = () => {
  const [loading, setLoading] = useState(false);

  const handleRequestPasswordReset = async (values: { email: string }) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/request_password_reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: values.email }),
      });

      if (response.ok) {
        message.success('Password reset link has been sent to your email.');
      } else {
        const errorData = await response.json();
        message.error('Failed to send reset link. Please try again.');
      }
    } catch (error) {
      message.error('An error occurred while requesting password reset.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
      <h2>Forgot Password</h2>
      <Form layout="vertical" onFinish={handleRequestPasswordReset}>
        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please enter your email' },
            { type: 'email', message: 'Please enter a valid email' },
          ]}
        >
          <Input placeholder="Enter your email" />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>
          Request Password Reset
        </Button>
      </Form>
    </div>
  );
};

export default ForgotPassword;
