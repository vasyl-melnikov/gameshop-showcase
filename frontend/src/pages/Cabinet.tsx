import React, { useState, useEffect, useContext } from 'react';
import { Card, Statistic, Tabs, Button, Form, Input, message } from 'antd';
import { Orders } from '../pages/Orders';
import { Tickets } from '../pages/Tickets';
import { API_BASE_URL } from '../config';
import { useNavigate } from 'react-router';
import { User } from '../context/UserContext';

interface CabinetProps {
  user: User
}

const Cabinet: React.FC<CabinetProps> = ({user}) => {
  const [newEmail, setNewEmail] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [isMfaVisible, setIsMfaVisible] = useState(false);

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isPasswordMfaVisible, setIsPasswordMfaVisible] = useState(false);

  const [isMfaFor2FASetupVisible, setisMfaFor2FASetupVisible] = useState(false);
  console.log(user);

  // Email change request and MFA flow
  const handleEmailChangeRequest = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/request_change_email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ email: newEmail }),
      });

      if (response.ok) {
        setIsMfaVisible(true); // Replace email input with MFA code input
        message.success('Confirmation email sent. Please enter the MFA code.');
      } else if (response.status === 400) {
        message.error('Invalid email or other request error.');
      } else {
        message.error('Failed to request email change');
      }
    } catch (error) {
      message.error('An error occurred while requesting email change');
    }
  };

  const handleMfaCodeSubmitForEmail = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/change_email`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ code: mfaCode }),
      });

      if (response.ok) {
        message.success('Your email has been changed successfully');
        setIsMfaVisible(false);
        user.email = newEmail;
      } else {
        message.error('Failed to change email, please check your MFA code');
      }
    } catch (error) {
      message.error('An error occurred while changing email');
    }
    setMfaCode("");
    setNewEmail("");
  };

  // Password change request and MFA flow
  const handlePasswordChangeRequest = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/request_change_password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
      });

      if (response.ok) {
        setIsPasswordMfaVisible(true); // Replace password inputs with MFA code input
        message.success('Password change requested. Please enter the MFA code.');
      } else if (response.status === 400) {
        message.error('Old password is incorrect or other request error.');
      } else {
        message.error('Failed to request password change');
      }
    } catch (error) {
      message.error('An error occurred while requesting password change');
    }
  };

  const handleMfaCodeSubmitForPassword = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/change_password`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ code: mfaCode }),
      });

      if (response.ok) {
        message.success('Your password has been changed successfully');
        setIsPasswordMfaVisible(false);
      } else {
        message.error('Failed to change password, please check your MFA code');
      }
    } catch (error) {
      message.error('An error occurred while changing password');
    }
    setMfaCode("");
    setNewPassword("");
    setOldPassword("");
  };

  const handleEnable2FA = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/request_enable_2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (response.ok) {
        setisMfaFor2FASetupVisible(true); // Replace email input with MFA code input
        message.success('Confirmation email sent. Please enter the MFA code.');
      } else if (response.status === 400) {
        message.error('Invalid email or other request error.');
      } else {
        message.error('Failed to request email change');
      }
    } catch (error) {
      message.error('An error occurred while requesting email change');
    }
  };

  const handleDisable2FA = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/request_disable_2fa`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
      });

      if (response.ok) {
        setisMfaFor2FASetupVisible(true); // Replace email input with MFA code input
        message.success('Confirmation email sent. Please enter the MFA code.');
      } else if (response.status === 400) {
        message.error('Invalid email or other request error.');
      } else {
        message.error('Failed to request email change');
      }
    } catch (error) {
      message.error('An error occurred while requesting email change');
    }
  };

  const handleMfaCodeSubmitForEnable2FA = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/enable_2fa`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ code: mfaCode }),
      });

      if (response.ok) {
        message.success('2FA authentication has been set up successfully');
        setisMfaFor2FASetupVisible(false);
        user.mfa_enabled = true;
      } else {
        message.error('Failed to set up 2FA, please check your MFA code');
      }
    } catch (error) {
      message.error('An error occurred while setting up 2FA');
    }
    setMfaCode("");
  };

  const handleMfaCodeSubmitForDisable2FA = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/users/me/disable_2fa`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify({ code: mfaCode }),
      });

      if (response.ok) {
        message.success('2FA authentication has been disabled successfully');
        setisMfaFor2FASetupVisible(false);
        user.mfa_enabled = false;
      } else {
        message.error('Failed to disable 2FA, please check your MFA code');
      }
    } catch (error) {
      message.error('An error occurred while disabling 2FA');
    }
    setMfaCode("");
  };

  // New way to define Tabs with 'items' prop
  const tabItems = [
    {
      key: '1',
      label: 'Change Email', // Update tab key from 'tab' to 'label'
      children: (
        <Form layout="vertical">
          {!isMfaVisible ? (
            <>
              <Form.Item label="New Email" required>
                <Input
                  placeholder="Enter new email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                />
              </Form.Item>
              <Button type="primary" htmlType="submit" onClick={handleEmailChangeRequest}>Request Email Change</Button>
            </>
          ) : (
            <>
              <Form.Item label="MFA Code" required>
                <Input
                  placeholder="Enter MFA code"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                />
              </Form.Item>
              <Button type="primary" htmlType="submit" onClick={handleMfaCodeSubmitForEmail}>Submit MFA Code</Button>
            </>
          )}
        </Form>
      ),
    },
    {
      key: '2',
      label: 'Change Password', // Update tab key from 'tab' to 'label'
      children: (
        <Form layout="vertical" onFinish={!isPasswordMfaVisible ? handlePasswordChangeRequest: handleMfaCodeSubmitForPassword}>
          {!isPasswordMfaVisible ? (
            <>
              <Form.Item
                label="Old Password"
                name="oldPassword"
                rules={[
                  { required: true, message: 'Please enter your new password' },
                ]}>
                <Input.Password
                  placeholder="Enter old password"
                  value={oldPassword}
                  onChange={(e) => setOldPassword(e.target.value)}
                />
              </Form.Item>
              <Form.Item
                label="New Password"
                name="newPassword"
                rules={[
                  { required: true, message: 'Please enter your new password' },
                  { 
                    pattern: /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).{8,}$/,
                    message: 'Password must be at least 8 characters long, with at least one uppercase letter, one lowercase letter, and one number.'
                  }
                ]}
                hasFeedback
              >
                <Input.Password
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </Form.Item>
              <Form.Item
                label="Confirm Password"
                name="confirm_password"
                dependencies={['newPassword']}
                rules={[
                  { required: true, message: 'Please confirm your password' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('newPassword') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('Passwords do not match'));
                    },
                  }),
                ]}
                hasFeedback
              >
                <Input.Password placeholder="Confirm Password" />
              </Form.Item>

              <Button type="primary" htmlType="submit">
                Request Password Change
              </Button>
            </>
          ) : (
            <>
              <Form.Item label="MFA Code" required>
                <Input
                  placeholder="Enter MFA code"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                />
              </Form.Item>
              <Button type="primary" htmlType="submit">Submit MFA Code</Button>
            </>
          )}
        </Form>
      ),
    },
    {
      key: '3',
      label: '2FA', // Update tab key from 'tab' to 'label'
      children: (
        <Form layout="vertical">
          {!isMfaFor2FASetupVisible ? (
              user.mfa_enabled ? (
                <Button type="primary" htmlType="submit" onClick={handleDisable2FA}>Disable 2FA</Button>
              ) : (
                <Button type="primary" htmlType="submit" onClick={handleEnable2FA}>Enable 2FA</Button>
              )
          ) : (
            <>
               <Form.Item label="MFA Code" required>
                <Input
                  placeholder="Enter MFA code"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                />
              </Form.Item>
              <Button type="primary" htmlType="submit" onClick={user.mfa_enabled ? handleMfaCodeSubmitForDisable2FA : handleMfaCodeSubmitForEnable2FA}>Submit MFA Code</Button>
            </>
          )}
        </Form>
      ),
    },
    {
      key: '4',
      label: 'Orders History', // Update tab key from 'tab' to 'label'
      children: <Orders />,
    },
    {
      key: '5',
      label: 'Support Tickets', // Update tab key from 'tab' to 'label'
      children: <Tickets />,
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <h2>Personal Cabinet</h2>

      {/* Client Info and Statistics */}
      <Card style={{ marginBottom: '20px' }}>
        <h3>Client Information</h3>
        <p><strong>Username:</strong> {user?.username}</p>
        <p><strong>Email:</strong> {user?.email}</p>
      </Card>

      {/* Tabs with new 'items' prop */}
      <Tabs defaultActiveKey="1" items={tabItems} />
    </div>
  );
};

export default Cabinet;
