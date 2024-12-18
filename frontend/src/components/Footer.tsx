import React from 'react';
import { Layout } from 'antd';
import { Link } from 'react-router-dom';

const { Footer } = Layout;

const ShopFooter: React.FC = () => {
  return (
    <Footer style={{ textAlign: 'center' }}>
      Game Shop ©2024 Created by YourName
      <div style={{ marginTop: '10px' }}>
        <Link to="/help">Need Help?</Link>
      </div>
    </Footer>
  );
};

export default ShopFooter;
