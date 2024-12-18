// src/pages/Feedback.tsx
import React, { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { List, Form, Input, Button, Rate } from 'antd';

type Feedback = {
  username: string;
  comment: string;
  rating: number;
};

const FeedbackPage: React.FC = () => {
  const location = useLocation();
  const state = location.state as { title?: string };
  const title = state?.title || "Unknown Game";  // Use default value

  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [form] = Form.useForm();

  const handleSubmit = (values: Feedback) => {
    setFeedbacks([...feedbacks, values]);
    form.resetFields();
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Feedback for {title}</h1>
      
      {/* Feedback Form */}
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item name="username" label="Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="comment" label="Comment" rules={[{ required: true }]}>
          <Input.TextArea />
        </Form.Item>
        <Form.Item name="rating" label="Rating" rules={[{ required: true }]}>
          <Rate />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit">
            Submit Feedback
          </Button>
        </Form.Item>
      </Form>
      
      {/* Display feedback */}
      <List
        header={`${feedbacks.length} Reviews`}
        dataSource={feedbacks}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={<b>{item.username}</b>}
              description={
                <>
                  <Rate disabled defaultValue={item.rating} />
                  <p>{item.comment}</p>
                </>
              }
            />
          </List.Item>
        )}
      />
    </div>
  );
};

export default FeedbackPage;
