import React from 'react';
import { Layout } from 'antd';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import withAuth from './context/AuthContext';
import NavBar from './components/NavBar';
import Shop from './pages/Shop';
import Registration from './pages/Registration';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import ConvertTempUser from './pages/ConvertTempUser';
import GameDetail from './pages/GameDetail';
import Cabinet from './pages/Cabinet';
import Orders from './pages/Orders';
import VerifyCode from './pages/VerifyCode';
import LoginPage from './pages/Login';
import Help from './pages/Help';
import Admin from './pages/Admin';
import ShopFooter from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import { CartProvider } from './context/CartContext';
import { UserProvider } from './context/UserContext';
import { Roles } from './constants/roles';

const { Header, Content } = Layout;

const AdminWithAuth = withAuth((props: any) => (
  <ProtectedRoute user={props.user} requiredRole={Roles.SUPPORT_MODERATOR}>
    <Admin user={props.user}/>
  </ProtectedRoute>
));

const CabinetWithAuth = withAuth((props: any) => (
  <ProtectedRoute user={props.user} requiredRole={Roles.USER}>
    <Cabinet user={props.user} />
  </ProtectedRoute>
));

const App: React.FC = () => {
  return (
    <Router>
      <CartProvider>
        <Layout>
          <Header style={{ position: 'fixed', width: '100%', zIndex: 1 }}>
            <NavBar />
          </Header>
          <Content style={{ padding: '50px', marginTop: 64 }}>
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Shop />} />
              <Route path="/shop" element={<Shop />} />
              <Route path="/game/:title" element={<GameDetail />} />
              <Route path="/orders" element={<Orders />} />
              <Route path="/verify-code" element={<VerifyCode />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/help" element={<Help />} />
              <Route path="/about" element={<div>About Us Page</div>} />
              <Route path="/register" element={<Registration />} />
              <Route path="/convert-temporary" element={<ConvertTempUser />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />

              {/* Protected Routes */}
              <Route
                path="/cabinet"
                element={
                  <UserProvider>
                    <CabinetWithAuth />
                  </UserProvider>
                }
              />
              <Route
                path="/admin"
                element={
                  <UserProvider>
                    <AdminWithAuth />
                  </UserProvider>
                }
              />
            </Routes>
          </Content>
          <ShopFooter />
        </Layout>
      </CartProvider>
    </Router>
  );
};

export default App;
