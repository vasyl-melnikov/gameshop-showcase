// src/pages/Admin.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Tabs, Button, Form, Input, Select, Modal, AutoComplete, FormInstance, Tag, Table, Spin, message } from 'antd';
import { GameChangeRequests } from '../pages/GameChangeRequests';
import { API_BASE_URL } from '../config';
import { User } from '../context/UserContext';
import { Roles, roleWeightMapping } from '../constants/roles';
import Upload from 'antd/es/upload/Upload';
import UploadOutlined from '@ant-design/icons/lib/icons/UploadOutlined';

const { TabPane } = Tabs;

interface AdminProps {
  user: User
}

const hasRole = (requiredRole: Roles, userRole: string) => {
  return roleWeightMapping[requiredRole] <= roleWeightMapping[userRole as Roles];
}

const Admin: React.FC<AdminProps> = ({user}) => {

  const [targetInfo, setTargetInfo] = useState({
    email: ''
  });

  const [email, setEmail] = useState(targetInfo.email);

  {/* Role Change Funcs and Vars */}

  const [role, setRole] = useState<string | undefined>(undefined);
  const [pendingSteamGuardRequests, setPendingSteamGuardRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const [isSteamCodeModalVisible, setIsSteamCodeModalVisible] = useState(false);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const [code, setCode] = useState<string>('');

  // Fetch the list of Steam Guard requests for the admin panel
  useEffect(() => {
    if (hasRole(Roles.ADMIN, user.role)) {
      fetchSteamGuardRequests();
    }
  }, [user]);

  const fetchSteamGuardRequests = async () => {
    const limit = 50
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admins/me/steam-guard-requests?limit=${limit}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
        },
      });
      if (!response.ok) {
        throw new Error('No pending requests so far');
      }
      const data = await response.json();
      setPendingSteamGuardRequests(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteRequest = (requestId: string) => {
    setCurrentRequestId(requestId); // Set the current request ID for the modal
    setIsSteamCodeModalVisible(true); // Show the modal
  };

  const handleSubmitCode = async () => {
    if (!currentRequestId || !code) return; // Ensure we have both request ID and code

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admins/me/steam-guard-requests/${currentRequestId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        throw new Error('Failed to complete Steam Guard request');
      }

      // Refetch Steam Guard requests after completing one
      fetchSteamGuardRequests();

      // Close the modal after successful submission
      setIsSteamCodeModalVisible(false);
      setCode(''); // Clear the code input
    } catch (error) {
      console.error(error);
    }
  };

  const columns = [
    {
      title: 'Request ID',
      dataIndex: 'request_id',
      key: 'request_id',
    },
    {
      title: 'Account ID',
      dataIndex: 'account_id',
      key: 'account_id',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'geekblue';
        if (status === 'completed') color = 'green';
        if (status === 'pending') color = 'volcano';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: 'Action',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          type="primary"
          onClick={() => handleCompleteRequest(record.request_id)}
          disabled={record.status === 'completed'}
        >
          Complete
        </Button>
      ),
    },
  ];


  const getAvailableRoles = (currentRole: string) => {
  switch (currentRole) {
    case Roles.ROOT_ADMIN:
      return [Roles.ADMIN, Roles.SUPPORT_MODERATOR, Roles.USER];
    case Roles.ADMIN:
      return [Roles.SUPPORT_MODERATOR, Roles.USER];
    default:
      return [];
    }
  };

  const availableRoles = getAvailableRoles(user.role);

  const handleRoleChange = async (values: { email: string; role: string | undefined}) => {
      try {
          const response = await fetch(`${API_BASE_URL}/api/v1/admins/me/users/role`, {
              method: 'PATCH',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
              },
              body: JSON.stringify({ email: values.email, role: values.role }),
          });

          if (response.ok) {
              const updatedUser = await response.json();
              message.success('User role updated successfully:', updatedUser);

          } else {
              const errorData = await response.json();
              message.error('Error updating user role:', errorData);

          }
      } catch (error) {
          console.error('Network error:', error);

      }
  };


  {/* Add Game Funcs and Vars */}

  const [isAddGameModalVisible, setIsAddGameModalVisible] = useState(false);

  const handleOpenAddGameModal = () => {
    setIsAddGameModalVisible(true);
  };

  const handleCloseAddGameModal = () => {
    setIsAddGameModalVisible(false);
  };

  const handleAddGame = async ( values: {
    title: string;
    genre: string;
    release_date: Date;
    description: string;
    price: number;
  }) => {
    try {
        const formData = new FormData();

        formData.append('payload', JSON.stringify(values));

        // Append the image if it's selected
        if (fileList.length > 0) {
          formData.append('game_img', fileList[0]); // Append the selected file
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/games`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          },
          body: formData,
        });

      } catch (error) {
        console.error('Network error:', error);
      }
    handleCloseAddGameModal();
  };

  {/* Add Game Account Funcs and Vars */}

  const [isAddAccountModalVisible, setIsAddAccountModalVisible] = useState(false);

  const handleOpenAddAccountModal = () => {
      setIsAddAccountModalVisible(true);
  };

  const handleCloseAddAccountModal = () => {
      setIsAddAccountModalVisible(false);
  };

  const handleAddGameAccount = async ( values: {
    account_name: string;
    steam_id_64: number;
    email: string;
    password: string;
  }) => {
      try {
          const response = await fetch(`${API_BASE_URL}/api/v1/game-accounts`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
              },
          body: JSON.stringify(values),
          });

          if (response.ok) {
              message.success('Account added');
              handleCloseAddAccountModal(); // Close modal after success
          } else {
              const errorData = await response.json();
              message.error('Error adding game account:', errorData);
          }
      } catch (error) {
          console.error('Network error:', error);
      }
  };


  {/* Edit Game Funcs and Vars */}

  interface Game {
    id: number;
    title: string;
    genre: string;
    release_date: string;
    description: string;
    price: number;
  }

  const [isEditGameModalVisible, setIsEditGameModalVisible] = useState(false);
  const [gameOptions, setGameOptions] = useState<Game[]>([]);
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null);

  const formRef = useRef<FormInstance>(null);
  const [fileList, setFileList] = useState<any[]>([]); // For storing the selected image


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
  const handleSelectGame = async (gameId: number) => {
    try {
      // Fetch the selected game's details using the game ID
      const response = await fetch(`${API_BASE_URL}/api/v1/games/${gameId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Error fetching game details: ${response.statusText}`);
      }

      const gameDetails = await response.json();

      // Set the selected game and open the modal
      setSelectedGame(gameDetails);
      setIsEditGameModalVisible(true);
    } catch (error) {
      console.error('Failed to fetch game details:', error);
    }
  };

  // Handle modal close
  const handleCloseEditGameModal = () => {
    if (formRef.current) {
      formRef.current.resetFields(); // Reset form fields
    }
    setIsEditGameModalVisible(false);
    setSelectedGame(null);
  };

  useEffect(() => {
    if (isEditGameModalVisible && selectedGame) {
      // Update form fields when modal is visible and selected game is set
      if (formRef.current) {
        formRef.current.setFieldsValue(selectedGame);
      }
    }
  }, [isEditGameModalVisible, selectedGame]);

  // Handle form submission (edit game)
  const handleEditGame = async (values: {
    title: string;
    genre: string;
    release_date: Date;
    description: string;
    price: number;
    image: any;
  }) => {

    const requestBody = {
        changes: {
          title: values.title,
          genre: values.genre,
          release_date: values.release_date,
          description: values.description,
          price: values.price,
        },
    };

    if (hasRole(Roles.ADMIN, user.role)) {
      try {
        const formData = new FormData();

        formData.append('payload', JSON.stringify(requestBody));

        // Append the image if it's selected
        if (fileList.length > 0) {
          formData.append('game_img', fileList[0]); // Append the selected file
        }

        const response = await fetch(`${API_BASE_URL}/api/v1/games/${selectedGame.id}`, {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          },
          body: formData,
        });

        if (response.ok) {
          message.success('Game updated successfully');
        } else {
          const errorData = await response.json();
          message.error('Error updating game:', errorData);
        }
      } catch (error) {
        console.error('Network error:', error);
      }
    } else if (hasRole(Roles.SUPPORT_MODERATOR, user.role)) {
      try {
        const formData = new FormData();

        formData.append('payload', JSON.stringify(requestBody));

        // Append the image if it's selected
        if (fileList.length > 0) {
          formData.append('game_img', fileList[0]); // Append the selected file
        }

        // Use the ID from the selected game
        const response = await fetch(`${API_BASE_URL}/api/v1/games/${selectedGame.id}/moderator-requests`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          },
          body: formData,
        });

        if (response.ok) {
          message.success('Game update request sent successfully');
          // Optionally, you can display a success message
        } else {
          const errorData = await response.json();
          message.error('Error requesting update for game:', errorData);
        }
      } catch (error) {
        console.error('Network error:', error);
      }
    }

    handleCloseEditGameModal();
  };

  {/* Add Games to Account Funcs and Vars */}

  const [isAddGamesModalVisible, setIsAddGamesModalVisible] = useState(false);
  const [selectedGameIds, setSelectedGameIds] = useState<number[]>([]);

  // Open and close modal
  const handleOpenAddGamesModal = () => setIsAddGamesModalVisible(true);
  const handleCloseAddGamesModal = () => setIsAddGamesModalVisible(false);

  // Handle game selection, adding game ID to list
  const handleSelectGameForAccount = (gameId: number) => {
    setSelectedGameIds((prevIds) => [...prevIds, gameId]);
  };

  // Remove game ID from the list
  const handleRemoveGameId = (gameId: number) => {
    setSelectedGameIds((prevIds) => prevIds.filter((id) => id !== gameId));
  };

  const handleAddGamesToAccount = async (values: { account_id: number }) => {
    const requestBody = {
      account_id: values.account_id,
      game_ids: selectedGameIds,
    };

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/game-accounts/games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        message.success('Games added successfully');
        setSelectedGameIds([]); // Clear selected game IDs after successful submission
      } else {
        const errorData = await response.json();
        message.error('Error adding games to account:', errorData);
      }
    } catch (error) {
      console.error('Network error:', error);
    }

    handleCloseAddGamesModal();
  };


  return (
    <div style={{ padding: '20px' }}>
      <h2>Admin Panel</h2>

      <Tabs defaultActiveKey="1">
        {hasRole(Roles.ADMIN, user.role) && (
          <TabPane tab="Change Role" key="1">
              <Form onFinish={() => handleRoleChange({ email, role })}>
                  <Form.Item label="Email" required>
                      <Input
                          placeholder="Enter email address"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                      />
                  </Form.Item>
                  <Form.Item label="Role" required>
                      <Select
                          placeholder="Select role"
                          value={role}
                          onChange={(value) => setRole(value)}
                      >
                          {availableRoles.map((role) => (
                              <Select.Option key={role} value={role}>
                                  {role}
                              </Select.Option>
                          ))}
                      </Select>
                  </Form.Item>
                  <Button type="primary" htmlType="submit">
                      Change Role
                  </Button>
              </Form>
          </TabPane>)}

        {/* Game Change Tab */}
        <TabPane tab="Edit Existing Game" key="2">
          {/* Input to search and select existing game */}
          <AutoComplete
            style={{ width: 300 }}
            options={gameOptions.map((game) => ({
              value: game.title, // This is what the user sees in the dropdown
              id: game.id,       // Store the id for reference
            }))}
            onSearch={handleSearch}
            onSelect={(value, option) => {
              // `option` contains the full object, including the id
              handleSelectGame(option.id); // Pass the game ID directly to the handler
            }}
            placeholder="Enter game name"
          />
        </TabPane>

        {hasRole(Roles.ADMIN, user.role) && (
          <>
            <TabPane tab="Game change requests" key="3">
              <GameChangeRequests/>
            </TabPane>
            {/* Steam Guard Requests Tab */}
            <TabPane tab="Steam Guard Requests" key="4">
              {loading ? (
                <Spin tip="Loading Steam Guard requests..." />
              ) : (
                <Table
                  dataSource={pendingSteamGuardRequests}
                  columns={columns}
                  rowKey="request_id"
                />
              )}
            </TabPane>
          </>
        )}
      </Tabs>
      {/* Modal for submitting Steam Guard code */}
      <Modal
        title="Enter Steam Guard Code"
        visible={isSteamCodeModalVisible}
        onOk={handleSubmitCode}
        onCancel={() => setIsSteamCodeModalVisible(false)}
        okText="Submit"
        cancelText="Cancel"
      >
        <Form layout="vertical">
          <Form.Item label="Steam Guard Code" required>
            <Input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter the code"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Button to open Add Account modal */}

      {hasRole(Roles.ADMIN, user.role) && (
          <Button
              type="primary"
              onClick={handleOpenAddAccountModal}
              style={{
                  position: 'absolute',
                  top: 170,
                  right: 183,
                  margin: '10px',
                  zIndex: 1,
              }}
          >
              Add Game Account
          </Button>
      )}

      {/* Modal for adding game account */}
      <Modal
          title="Add New Game Account"
          visible={isAddAccountModalVisible}
          onCancel={handleCloseAddAccountModal}
          footer={null}
          style={{ backdropFilter: 'blur(10px)' }}
      >
          <Form onFinish={handleAddGameAccount}>
              <Form.Item label="Account Name" name="account_name" rules={[{ required: true, message: 'Please enter the account name' }]}>
                  <Input placeholder="Enter account name" maxLength={49} />
              </Form.Item>
              <Form.Item label="Steam ID 64" name="steam_id_64" rules={[{ required: true, message: 'Please enter the Steam ID 64' }]}>
                  <Input type="number" placeholder="Enter Steam ID 64" />
              </Form.Item>
              <Form.Item label="Email" name="email" rules={[{ required: true, message: 'Please enter the email' }]}>
                  <Input type="email" placeholder="Enter email" />
              </Form.Item>
              <Form.Item label="Password" name="password" rules={[{ required: true, message: 'Please enter the password' }]}>
                  <Input type="password" placeholder="Enter password" />
              </Form.Item>
              <Button type="primary" htmlType="submit">
                  Add Game Account
              </Button>
          </Form>
      </Modal>


      {/* Button to open Add Games to Account modal */}
      {hasRole(Roles.ADMIN, user.role) && (
        <Button
          type="primary"
          onClick={handleOpenAddGamesModal}
          style={{
            position: 'absolute',
            top: 170,
            right: 353,
            margin: '10px',
            zIndex: 1,
          }}
        >
          Add Games to Account
        </Button>
      )}

      {/* Modal for adding games to an account */}
      <Modal
        title="Add Games to Account"
        visible={isAddGamesModalVisible}
        onCancel={handleCloseAddGamesModal}
        footer={null}
        style={{ backdropFilter: 'blur(10px)' }}
      >
        <Form onFinish={handleAddGamesToAccount}>
          <Form.Item label="Account ID" name="account_id" rules={[{ required: true, message: 'Please enter the account ID' }]}>
            <Input placeholder="Enter account ID" type="number" />
          </Form.Item>
          <Form.Item label="Select Games" name="game_ids">
            <AutoComplete
              style={{ width: '100%' }}
              options={gameOptions.map((game) => ({
                value: game.title,
                id: game.id,
              }))}
              onSearch={handleSearch}
              onSelect={(value, option) => handleSelectGameForAccount(option.id)} // Add game ID to list
              placeholder="Search and select games"
            />
          </Form.Item>
          <Form.Item>
            <div>
              <h4>Selected Game IDs:</h4>
              {selectedGameIds.map((id) => (
                <Tag key={id} closable onClose={() => handleRemoveGameId(id)}>
                  {id}
                </Tag>
              ))}
            </div>
          </Form.Item>
          <Button type="primary" htmlType="submit">
            Add Games
          </Button>
        </Form>
      </Modal>

      {/* Button to open Add Game modal */}
      {hasRole(Roles.ADMIN, user.role) && (
        <Button
          type="primary"
          onClick={handleOpenAddGameModal}
          style={{
            position: 'absolute',
            top: 170,
            right: 63,
            margin: '10px',
            zIndex: 1,
          }}
        >
          Add Game
        </Button>
      )}

      {/* Modal for adding game */}
      <Modal
        title="Add New Game"
        visible={isAddGameModalVisible}
        onCancel={handleCloseAddGameModal}
        footer={null}
        style={{ backdropFilter: 'blur(10px)' }}
      >
        <Form onFinish={handleAddGame}>
          <Form.Item label="Game Title" name="title" rules={[{ required: true, message: 'Please enter the game title' }]}>
            <Input placeholder="Enter game name" maxLength={49} />
          </Form.Item>
          <Form.Item label="Genre" name="genre" rules={[{ required: true, message: 'Please enter the game genre' }]}>
            <Input placeholder="Enter game genre" />
          </Form.Item>
          <Form.Item label="Release Date" name="release_date" rules={[{ required: true, message: 'Please enter the release date' }]}>
            <Input type="date" placeholder="Enter game price" />
          </Form.Item>
          <Form.Item
            label="Description"
            name="description"
            rules={[{ required: true, message: 'Please enter the description' }]}
          >
            <Input.TextArea
              placeholder="Enter description"
              maxLength={1000}
              autoSize={{ minRows: 3, maxRows: 5 }} // Adjusts the number of rows based on content
            />
          </Form.Item>
          <Form.Item label="Price" name="price" rules={[{ required: true, message: 'Please enter the game price' }]}>
            <Input type="number" placeholder="Enter game price" />
          </Form.Item>
          {/* Image Upload Field */}
          <Form.Item label="Upload New Image" name="image">
            <Upload
              fileList={fileList}
              beforeUpload={(file) => {
                setFileList([file]); // Set the selected file in the fileList state
                return false; // Prevent automatic upload, we'll handle it manually
              }}
              onRemove={() => setFileList([])} // Clear the fileList when the file is removed
              showUploadList={{ showRemoveIcon: true }}
              maxCount={1} // Only allow one file to be selected
            >
              <Button icon={<UploadOutlined />}>Click to Upload</Button>
            </Upload>
          </Form.Item>
          <Button type="primary" htmlType="submit">
            Add Game
          </Button>
        </Form>
      </Modal>

      {/* Modal for editing game */}
      <Modal
      title="Edit Game"
        visible={isEditGameModalVisible}
        onCancel={() => setIsEditGameModalVisible(false)}
        footer={null}
        style={{ backdropFilter: 'blur(10px)' }}
      >
        <Form ref={formRef} onFinish={handleEditGame}>
          <Form.Item label="Game Title" name="title" rules={[{ required: true, message: 'Please enter the game title' }]}>
            <Input placeholder="Enter game title" />
          </Form.Item>
          
          <Form.Item label="Genre" name="genre" rules={[{ required: true, message: 'Please enter the game genre' }]}>
            <Input placeholder="Enter game genre" />
          </Form.Item>
          
          <Form.Item label="Release Date" name="release_date" rules={[{ required: true, message: 'Please enter the release date' }]}>
            <Input type="date" placeholder="Enter release date" />
          </Form.Item>

          <Form.Item
            label="Description"
            name="description"
            rules={[{ required: true, message: 'Please enter the description' }]}
          >
            <Input.TextArea
              placeholder="Enter description"
              maxLength={200}
              autoSize={{ minRows: 3, maxRows: 5 }}
            />
          </Form.Item>

          <Form.Item label="Price" name="price" rules={[{ required: true, message: 'Please enter the game price' }]}>
            <Input type="number" placeholder="Enter game price" />
          </Form.Item>

          {/* Image Upload Field */}
          <Form.Item label="Upload New Image" name="image">
            <Upload
              fileList={fileList}
              beforeUpload={(file) => {
                setFileList([file]); // Set the selected file in the fileList state
                return false; // Prevent automatic upload, we'll handle it manually
              }}
              onRemove={() => setFileList([])} // Clear the fileList when the file is removed
              showUploadList={{ showRemoveIcon: true }}
              maxCount={1} // Only allow one file to be selected
            >
              <Button icon={<UploadOutlined />}>Click to Upload</Button>
            </Upload>
          </Form.Item>

          <Button type="primary" htmlType="submit">
            Save Changes
          </Button>
        </Form>
      </Modal>
    </div>
  );
};

export default Admin;
