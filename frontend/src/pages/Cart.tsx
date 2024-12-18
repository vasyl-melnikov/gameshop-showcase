// src/pages/Cart.tsx
import React, { useContext } from 'react';
import { Row, Col, List, InputNumber, Button } from 'antd';
import { CartContext } from '../context/CartContext';

const Cart: React.FC = () => {
  const cartContext = useContext(CartContext);

  if (!cartContext) return null;

  const { cart, updateQuantity, removeFromCart } = cartContext;

  return (
    <div style={{ padding: '20px' }}>
      <h1>Your Cart</h1>
      {cart.length === 0 ? (
        <p>Your cart is empty</p>
      ) : (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <List
              itemLayout="horizontal"
              dataSource={cart}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <InputNumber
                      min={1}
                      defaultValue={item.quantity}
                      onChange={(value) => updateQuantity(item.title, value as number)}
                    />,
                    <Button type="dashed" onClick={() => removeFromCart(item.title)}>
                      Remove
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={<img src={"item.imgSrc"} alt={item.title} width={100} />}
                    title={item.title}
                    description={`${item.description} - Quantity: ${item.quantity}`}
                  />
                </List.Item>
              )}
            />
          </Col>
        </Row>
      )}
    </div>
  );
};

export default Cart;
