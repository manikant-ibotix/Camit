import { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Box,
  CircularProgress,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import VideocamIcon from '@mui/icons-material/Videocam';
import PeopleIcon from '@mui/icons-material/People';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { cameraAPI, alertAPI } from '../services/api';
import { toast } from 'react-toastify';

export default function Dashboard() {
  const [cameras, setCameras] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [camerasRes, statsRes] = await Promise.all([
        cameraAPI.getAll(),
        alertAPI.getStats(7),
      ]);
      setCameras(camerasRes.data);
      setStats(statsRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const activeCameras = cameras.filter((c) => c.status === 'active').length;
  const todayAlerts = stats?.today_alerts || 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Cameras
                  </Typography>
                  <Typography variant="h4">{cameras.length}</Typography>
                </Box>
                <VideocamIcon sx={{ fontSize: 48, color: 'primary.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Active Cameras
                  </Typography>
                  <Typography variant="h4">{activeCameras}</Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Today's Alerts
                  </Typography>
                  <Typography variant="h4">{todayAlerts}</Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 48, color: 'warning.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Week Total
                  </Typography>
                  <Typography variant="h4">{stats?.total_alerts || 0}</Typography>
                </Box>
                <PeopleIcon sx={{ fontSize: 48, color: 'error.main' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alert Types Breakdown */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Alert Types (Last 7 Days)
        </Typography>
        <Grid container spacing={2}>
          {stats?.alerts_by_type && Object.entries(stats.alerts_by_type).map(([type, count]) => (
            <Grid item xs={6} sm={3} key={type}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="textSecondary" variant="body2">
                    {type.toUpperCase()}
                  </Typography>
                  <Typography variant="h5">{count}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* Camera Status */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Camera Status
        </Typography>
        {cameras.length === 0 ? (
          <Typography color="textSecondary">
            No cameras configured. Go to Cameras page to add cameras.
          </Typography>
        ) : (
          <Box>
            {cameras.map((camera) => (
              <Box
                key={camera.id}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  p: 2,
                  mb: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                }}
              >
                <Box>
                  <Typography variant="subtitle1">{camera.name}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {camera.location || 'No location'}
                  </Typography>
                </Box>
                <Box
                  sx={{
                    px: 2,
                    py: 0.5,
                    borderRadius: 1,
                    bgcolor:
                      camera.status === 'active'
                        ? 'success.light'
                        : camera.status === 'error'
                        ? 'error.light'
                        : 'grey.300',
                  }}
                >
                  <Typography variant="body2" fontWeight="bold">
                    {camera.status.toUpperCase()}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
}
