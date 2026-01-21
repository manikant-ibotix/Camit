import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Alerts from './pages/Alerts';
import VideoAnalysis from './pages/VideoAnalysis';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cameras" element={<Cameras />} />
            <Route path="/analysis" element={<VideoAnalysis />} />
            <Route path="/alerts" element={<Alerts />} />
          </Routes>
        </Layout>
      </Router>
      <ToastContainer position="top-right" autoClose={5000} />
    </ThemeProvider>
  );
}

export default App;
