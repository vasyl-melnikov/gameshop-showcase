// src/components/NavBar.tsx
import React, { useContext, useState } from 'react';
import { Menu, Badge, AutoComplete, message } from 'antd';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShoppingCartOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { API_BASE_URL } from '../config';
import { CartContext } from '../context/CartContext';

const NavBar: React.FC = () => {
  const cartContext = useContext(CartContext);
  const navigate = useNavigate();
  const location = useLocation();
  const HIDDEN_SEARCH_BAR_PATHS = ['/cabinet', '/admin'];

  const cartItemCount = cartContext?.cart.reduce((total, item) => total + item.quantity, 0) || 0;

  const handleUserIconClick = () => {
      navigate('/cabinet');
  };

  const menuItems = [
    {
      key: 'shop',
      label: <Link to="/shop">Shop</Link>,
    },
    {
      key: 'about',
      label: <Link to="/about">About Us</Link>,
    },
  ];

  interface Game {
    id: number;
    title: string;
    genre: string;
    release_date: string;
    description: string;
    price: string;
  }

  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);
  const [gameOptions, setGameOptions] = useState<Game[]>([]);

  const handleLogout = () => {
      if (localStorage.getItem('authToken')) {
          localStorage.removeItem('authToken');
          message.success('Logged out')
          navigate('/login');
      }
  };

  const fetchGames = async (searchTerm: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/games/search?search_term=${searchTerm}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error fetching games: ${response.statusText}`);
      }

      const data = await response.json();
      const filteredGames = data
        .filter((game: Game) => game.title.toLowerCase().includes(searchTerm.toLowerCase()))
        .slice(0, 5); // Limit results to 5
      setGameOptions(filteredGames);
    } catch (error) {
      console.error('Failed to fetch games:', error);
    }
  };

  // Handle game search input change
  const handleSearch = (value: string) => {
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }

    setSearchTimeout(
      setTimeout(() => {
        if (value) {
          fetchGames(value);
        } else {
          setGameOptions([]);
        }
      }, 500) // 500ms delay
    );
  };

  // Handle game selection
  const handleSelectGame = async (gameTitle: string) => {
      const selectedGame = gameOptions.find((game) => game.title === gameTitle);
      if (selectedGame) {
        navigate(`/game/${selectedGame.title}`, {
          state: {
            title: selectedGame.title,
            description: selectedGame.description,
            //imgSrc: selectedGame.imgSrc,
            price: parseFloat(selectedGame.price),
            //rating: selectedGame.rating,
          }
        });
      }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 20px', backgroundColor: '#1f2937' }}>
      {/* Menu Items */}
      <Menu
        mode="horizontal"
        items={menuItems}
        style={{ backgroundColor: 'transparent', flex: 1, borderBottom: 'none' }}
        theme="dark"
      />

      {/* Search Autocomplete */}
      {!HIDDEN_SEARCH_BAR_PATHS.includes(location.pathname) && (
        <AutoComplete
          style={{ width: 300, marginRight: '20px' }}
          options={gameOptions.map((game) => ({
            value: game.title, // This will be displayed in the dropdown
            id: game.id,       // Store the id for navigation
          }))}
          onSearch={handleSearch}
          onSelect={handleSelectGame}
          placeholder="Search for a game"
        />
      )}

      {/* Cart and User Icons aligned to the right */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        {/*
            <Link to="/cart" style={{ marginRight: '20px' }}>
          <Badge count={cartItemCount} overflowCount={99}>
            <ShoppingCartOutlined 
              style={{ fontSize: '25px', color: '#fff', verticalAlign: 'middle'}}  // Adjusted font size
            />
          </Badge>
        </Link>
        */}


        {/* User Icon */}
        <UserOutlined 
          style={{ fontSize: '22px', color: '#fff', verticalAlign: 'middle', cursor: 'pointer' }} // Same font size as Cart icon
          onClick={handleUserIconClick}
        />
        {/* Logout Button */}
        <LogoutOutlined
          style={{ marginLeft: '15px', fontSize: '22px', color: '#fff', verticalAlign: 'middle', cursor: 'pointer' }}
          onClick={handleLogout}
        />
      </div>
    </div>
  );
};

export default NavBar;
