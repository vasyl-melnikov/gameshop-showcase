import React, { useEffect, useState } from 'react';
import { Row, Col, Pagination, message } from 'antd';
import { API_BASE_URL } from '../config';
import GameCard from '../components/GameCard';

const Shop: React.FC = () => {
  type GameCardProps = {
    id: number;
    title: string;
    genre: string;
    release_date: string;
    description: string;
    game_img_url: string;
    price: string;       // Add price prop
  };

  const [games, setGames] = useState<GameCardProps[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [total, setTotal] = useState(0);    // total games available
  const pageSize = 12;

  useEffect(() => {
    // Function to fetch game count
    const fetchGameCount = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/games/count`); // Call the API
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }
        const data = await response.json();
        setTotal(data.count);
      } catch (err) {
        console.log(err)
      }
    };

    fetchGameCount(); // Invoke the function
  }, []);

  useEffect(() => {
    fetchGames(currentPage);
  }, [currentPage]);

  const fetchGames = async (page: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/games?page=${page}&page_size=${pageSize}`);
      const data = await response.json();
      console.log(data)
      setGames(data);
    } catch (error) {
      message.error('Failed to fetch games');
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>Game Shop</h1>
      <Row gutter={[16, 16]}>
        {games.map((game) => (
          <Col key={game.title} xs={24} sm={12} md={8} lg={6}>
            <GameCard
              id={game.id}
              title={game.title}
              genre={game.genre}
              release_date={game.release_date}
              description={game.description}
              price={parseFloat(game.price)}
              imgSrc={game.game_img_url}
            />
          </Col>
        ))}
      </Row>
      <Pagination
        current={currentPage}
        pageSize={pageSize}
        onChange={handlePageChange}
        total={total}
        showSizeChanger={false}
        style={{ textAlign: 'center', marginTop: '20px' }}
      />
    </div>
  );
};

export default Shop;
