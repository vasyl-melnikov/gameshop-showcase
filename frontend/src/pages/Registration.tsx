import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

const Registration: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegistration = async (values: {
    first_name?: string;
    last_name?: string;
    username: string;
    email: string;
    password: string;
  }) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success('Registration successful!');
        navigate('/login');
      } else {
        const errorData = await response.json();
        const errorMessage = errorData?.detail || 'Registration failed. Please try again.';
        message.error(errorMessage);
      }
    } catch (error) {
      message.error('An error occurred during registration.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '0 auto', padding: '20px' }}>
      <h2>Registration</h2>
      <Form layout="vertical" onFinish={handleRegistration}>
        <Form.Item label="First Name" name="first_name">
          <Input placeholder="First Name" />
        </Form.Item>

        <Form.Item label="Last Name" name="last_name">
          <Input placeholder="Last Name" />
        </Form.Item>

        <Form.Item
          label="Username"
          name="username"
          rules={[{ required: true, message: 'Please enter your username' }]}
        >
          <Input placeholder="Username" />
        </Form.Item>

        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please enter your email' },
            { type: 'email', message: 'Please enter a valid email' },
          ]}
        >
          <Input placeholder="Email" />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[
            { required: true, message: 'Please enter your password' },
            {
              pattern: /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$/,
              message:
                'Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one number.',
            },
          ]}
          hasFeedback
        >
          <Input.Password placeholder="Password" />
        </Form.Item>

        <Form.Item
          label="Confirm Password"
          name="confirm_password"
          dependencies={['password']}
          hasFeedback
          rules={[
            { required: true, message: 'Please confirm your password' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Passwords do not match'));
              },
            }),
          ]}
        >
          <Input.Password placeholder="Confirm Password" />
        </Form.Item>

        <Button type="primary" htmlType="submit" loading={loading} block>
          Register
        </Button>
      </Form>
    </div>
  );
};

export default Registration;
