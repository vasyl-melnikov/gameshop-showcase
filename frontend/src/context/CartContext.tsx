// src/context/CartContext.tsx
import React, { createContext, useState, ReactNode } from 'react';

type CartItem = {   //imgSrc
  title: string;
  description: string;
  quantity: number;
};

type CartContextType = {
  cart: CartItem[];
  addToCart: (item: CartItem) => void;
  updateQuantity: (title: string, quantity: number) => void;
  removeFromCart: (title: string) => void;
};

export const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [cart, setCart] = useState<CartItem[]>([]);

  const addToCart = (newItem: CartItem) => {
    setCart((prevCart) => {
      const existingItem = prevCart.find(item => item.title === newItem.title);
      if (existingItem) {
        // Update quantity if item already exists
        return prevCart.map(item =>
          item.title === newItem.title
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        return [...prevCart, { ...newItem, quantity: 1 }];
      }
    });
  };

  const updateQuantity = (title: string, quantity: number) => {
    setCart((prevCart) =>
      prevCart.map(item =>
        item.title === title ? { ...item, quantity } : item
      )
    );
  };

  const removeFromCart = (title: string) => {
    setCart((prevCart) => prevCart.filter(item => item.title !== title));
  };

  return (
    <CartContext.Provider value={{ cart, addToCart, updateQuantity, removeFromCart }}>
      {children}
    </CartContext.Provider>
  );
};
