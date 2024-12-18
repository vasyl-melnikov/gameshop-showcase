import React, { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { useNavigate, Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [temporaryToken, setTemporaryToken] = useState<string | null>(null);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: values.email,
          password: values.password,
        }),
      });

      const data = await response.json();
      const mfaHeader = response.headers.get('X-Mfa-Required');

      if (response.ok) {
        if (mfaHeader && mfaHeader.toLowerCase() === 'true') {
          setTemporaryToken(data.access_token);
          setMfaRequired(true);
          message.info('Multi-factor authentication required. Please enter your MFA code.');
        } else {
          localStorage.setItem('authToken', data.access_token);
          message.success('Login successful');

          const lastVisitedPage = localStorage.getItem('lastVisitedPage');  // redirect to last page
          localStorage.removeItem('lastVisitedPage');
          navigate(lastVisitedPage || '/cabinet');
        }
      } else {
        message.error(data.message || 'Login failed');
      }
    } catch (error) {
      message.error('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const onMfaFinish = async (values: any) => {
    if (!temporaryToken) return;

    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/login/auth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${temporaryToken}`,
        },
        body: JSON.stringify({
          code: values.code,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('authToken', data.access_token);
        message.success('Login successful');

        const lastVisitedPage = localStorage.getItem('lastVisitedPage');  // redirect to last page
        localStorage.removeItem('lastVisitedPage');
        navigate(lastVisitedPage || '/cabinet');
      } else {
        message.error(data.message || 'MFA verification failed');
      }
    } catch (error) {
      message.error('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto' }}>
      <h2>{mfaRequired ? 'Enter MFA Code' : 'Login'}</h2>
      <Form onFinish={mfaRequired ? onMfaFinish : onFinish}>
        {mfaRequired ? (
          <Form.Item
            name="code"
            rules={[{ required: true, message: 'Please enter your MFA code' }]}
          >
            <Input placeholder="MFA Code" />
          </Form.Item>
        ) : (
          <>
            <Form.Item
              name="email"
              rules={[{ required: true, message: 'Please enter your email' }]}
            >
              <Input placeholder="Email" />
            </Form.Item>
            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please enter your password' }]}
            >
              <Input.Password placeholder="Password" />
            </Form.Item>
          </>
        )}
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            {mfaRequired ? 'Verify MFA Code' : 'Login'}
          </Button>
        </Form.Item>
      </Form>
      {!mfaRequired && (
        <div style={{ textAlign: 'center', marginTop: '10px' }}>
          <p>
            Don’t have an account? <Link to="/register">Register here</Link>
          </p>
          <p>
            Made a purchase without an account? <Link to="/convert-temporary">Register Here</Link> using your used email to access your orders
          </p>
          <p>
            <Link to="/forgot-password">Forgot Password?</Link>
          </p>
        </div>
      )}
    </div>
  );
};

export default Login;
