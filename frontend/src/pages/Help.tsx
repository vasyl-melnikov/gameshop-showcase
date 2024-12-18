import React, { useEffect } from 'react';

const Help: React.FC = () => {
  useEffect(() => {
    const script = document.createElement("script");
    script.src = "https://embed.tawk.to/67001ca437379df10df1e547/1i9c6vp78";
    script.async = true;
    script.charset = "UTF-8";
    script.setAttribute("crossorigin", "*");
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div style={{ padding: '20px', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
      {/* FAQ Section */}
      <section style={{ marginBottom: '40px' }}>
        <h1>Frequently Asked Questions (FAQ)</h1>
        <ul style={{ textAlign: 'left' }}>
          <li><strong>Question 1:</strong> How can I reset my password?</li>
          <p>Answer: You can reset your password by clicking on "Forgot Password" on the login page and following the instructions.</p>

          <li><strong>Question 2:</strong> How can I track my order?</li>
          <p>Answer: You can track your order by visiting the "Orders" section in your account.</p>

          <li><strong>Question 3:</strong> What is your return policy?</li>
          <p>Answer: You can return products within 30 days of purchase if they are in original condition.</p>
        </ul>
      </section>

      {/* Contact Support Section */}
      <section>
        <h2>Contact Support</h2>
        <p>If you need further assistance, please contact our support team:</p>
        <form style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: '10px' }}>
            <label htmlFor="name">Name:</label><br />
            <input type="text" id="name" name="name" style={{ width: '100%', padding: '8px' }} />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label htmlFor="email">Email:</label><br />
            <input type="email" id="email" name="email" style={{ width: '100%', padding: '8px' }} />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label htmlFor="message">Message:</label><br />
            <textarea id="message" name="message" rows={5} style={{ width: '100%', padding: '8px' }}></textarea>
          </div>
          <button type="submit" style={{ padding: '10px 20px', backgroundColor: '#1890ff', color: '#fff', border: 'none', cursor: 'pointer' }}>
            Submit
          </button>
        </form>
      </section>
    </div>
  );
};

export default Help;
