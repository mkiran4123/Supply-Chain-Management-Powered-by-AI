import axios from 'axios';
import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Grid, 
  Paper, 
  Typography, 
  Card, 
  CardContent, 
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  Inventory as InventoryIcon, 
  ShoppingCart as OrderIcon, 
  People as SupplierIcon, 
  Warning as AlertIcon,
  Search as SearchIcon
} from '@mui/icons-material';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      console.log('Authentication error detected, redirecting to login');
      // Clear auth token
      localStorage.removeItem('authToken');
      // Redirect to login page
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/token', 
      `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  },
  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

// Inventory API
const inventoryAPI = {
  getAll: async () => {
    const response = await api.get('/inventory/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/inventory/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/inventory/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/inventory/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/inventory/${id}`);
  },
};

// Supplier API
const supplierAPI = {
  getAll: async () => {
    const response = await api.get('/suppliers/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/suppliers/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/suppliers/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/suppliers/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/suppliers/${id}`);
  },
};

// Order API
const orderAPI = {
  getAll: async () => {
    const response = await api.get('/orders/');
    return response.data;
  },
  getById: async (id) => {
    const response = await api.get(`/orders/${id}`);
    return response.data;
  },
  create: async (data) => {
    const response = await api.post('/orders/', data);
    return response.data;
  },
  update: async (id, data) => {
    const response = await api.put(`/orders/${id}`, data);
    return response.data;
  },
  delete: async (id) => {
    await api.delete(`/orders/${id}`);
  },
};

// AI Search API
const aiAPI = {
  search: async (query) => {
    const response = await api.post('/ai/search/', { query_text: query });
    return response.data;
  }
};

// Export all APIs
export { authAPI, inventoryAPI, supplierAPI, orderAPI, aiAPI };

const Dashboard = () => {
  // Mock useAuth until we find the actual implementation
  const useAuth = () => ({
    currentUser: { id: 1, name: 'User' },
    logActivity: (activity) => console.log('Activity logged:', activity)
  });
  
  const { currentUser, logActivity } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [searchError, setSearchError] = useState(null);

  // Function to handle search query changes
  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  // Function to handle search submission
  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setIsSearching(true);
    setSearchError(null);
    
    try {
      logActivity('Performed AI search: ' + searchQuery);
      
      // Call the AI search endpoint
      const response = await api.post('/ai/search/', { query_text: searchQuery });
      setSearchResults(response.data);
      setShowResults(true);
    } catch (error) {
      console.error('Error performing AI search:', error);
      setSearchError('Failed to perform search. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  // Function to handle Enter key press in search field
  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  // Function to close results dialog
  const handleCloseResults = () => {
    setShowResults(false);
  };

  // Load dashboard data on component mount
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch dashboard data from API
        // This is a placeholder - implement actual data fetching
        const data = {
          inventorySummary: { total: 120, lowStock: 15 },
          ordersSummary: { total: 45, pending: 12 },
          suppliersSummary: { total: 28, active: 22 },
          recentAlerts: [
            { id: 1, message: 'Low stock alert: Product A', severity: 'warning' },
            { id: 2, message: 'Order #1234 delayed', severity: 'error' },
          ]
        };
        
        setDashboardData(data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Render loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      {/* AI Search Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search using AI"
          value={searchQuery}
          onChange={handleSearchChange}
          onKeyPress={handleKeyPress}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton 
                  onClick={handleSearch} 
                  disabled={isSearching || !searchQuery.trim()}
                  aria-label="search"
                >
                  {isSearching ? <CircularProgress size={24} /> : <SearchIcon />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        {searchError && (
          <Typography color="error" variant="body2" sx={{ mt: 1 }}>
            {searchError}
          </Typography>
        )}
      </Paper>

      {/* Dashboard Content */}
      <Grid container spacing={3}>
        {/* Inventory Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Inventory" 
              avatar={<InventoryIcon color="primary" />} 
            />
            <CardContent>
              <Typography variant="h4">{dashboardData.inventorySummary.total}</Typography>
              <Typography variant="body2">Total Items</Typography>
              <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                {dashboardData.inventorySummary.lowStock} items low in stock
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Orders Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Orders" 
              avatar={<OrderIcon color="primary" />} 
            />
            <CardContent>
              <Typography variant="h4">{dashboardData.ordersSummary.total}</Typography>
              <Typography variant="body2">Total Orders</Typography>
              <Typography variant="body2" color="warning.main" sx={{ mt: 1 }}>
                {dashboardData.ordersSummary.pending} pending orders
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Suppliers Summary */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader 
              title="Suppliers" 
              avatar={<SupplierIcon color="primary" />} 
            />
            <CardContent>
              <Typography variant="h4">{dashboardData.suppliersSummary.total}</Typography>
              <Typography variant="body2">Total Suppliers</Typography>
              <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                {dashboardData.suppliersSummary.active} active suppliers
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Alerts */}
        <Grid item xs={12}>
          <Card>
            <CardHeader 
              title="Recent Alerts" 
              avatar={<AlertIcon color="error" />} 
            />
            <CardContent>
              <List>
                {dashboardData.recentAlerts.map((alert) => (
                  <ListItem key={alert.id}>
                    <ListItemText 
                      primary={alert.message} 
                      primaryTypographyProps={{ 
                        color: alert.severity === 'error' ? 'error' : 'warning.main' 
                      }} 
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search Results Dialog */}
      <Dialog 
        open={showResults} 
        onClose={handleCloseResults}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>AI Search Results</DialogTitle>
        <DialogContent>
          {searchResults ? (
            <>
              <Typography variant="subtitle1" gutterBottom>
                Query: "{searchQuery}"
              </Typography>
              <Divider sx={{ my: 2 }} />
              
              {searchResults.explanation && (
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {searchResults.explanation}
                </Typography>
              )}
              
              {searchResults.results && searchResults.results.length > 0 ? (
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        {Object.keys(searchResults.results[0]).map((key) => (
                          <TableCell key={key}>{key}</TableCell>
                        ))}
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {searchResults.results.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, i) => (
                            <TableCell key={i}>{value}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography>No results found.</Typography>
              )}
            </>
          ) : (
            <Typography>No results available.</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseResults}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
