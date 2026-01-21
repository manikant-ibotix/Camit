import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import { format } from 'date-fns';
import { alertAPI } from '../services/api';
import { toast } from 'react-toastify';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [filter]);

  const loadAlerts = async () => {
    try {
      const params = {};
      if (filter !== 'all') {
        params.alert_type = filter;
      }
      const response = await alertAPI.getAll(params);
      setAlerts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading alerts:', error);
      toast.error('Failed to load alerts');
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await alertAPI.acknowledge(id);
      toast.success('Alert acknowledged');
      loadAlerts();
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      toast.error('Failed to acknowledge alert');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      try {
        await alertAPI.delete(id);
        toast.success('Alert deleted');
        loadAlerts();
      } catch (error) {
        console.error('Error deleting alert:', error);
        toast.error('Failed to delete alert');
      }
    }
  };

  const getAlertColor = (type) => {
    switch (type) {
      case 'fall':
        return 'error';
      case 'lying':
        return 'warning';
      case 'pushing':
        return 'error';
      case 'crowd':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Alerts</Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Filter by Type</InputLabel>
          <Select
            value={filter}
            label="Filter by Type"
            onChange={(e) => setFilter(e.target.value)}
          >
            <MenuItem value="all">All Alerts</MenuItem>
            <MenuItem value="fall">Fall</MenuItem>
            <MenuItem value="lying">Lying</MenuItem>
            <MenuItem value="pushing">Pushing</MenuItem>
            <MenuItem value="crowd">Crowd</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Camera</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">No alerts found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              alerts.map((alert) => (
                <TableRow
                  key={alert.id}
                  sx={{
                    backgroundColor: alert.acknowledged ? 'inherit' : 'action.hover',
                  }}
                >
                  <TableCell>
                    {format(new Date(alert.created_at), 'MMM dd, yyyy HH:mm:ss')}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{alert.camera.name}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {alert.camera.location || 'No location'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={alert.alert_type.toUpperCase()}
                      color={getAlertColor(alert.alert_type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{(alert.confidence * 100).toFixed(1)}%</TableCell>
                  <TableCell>
                    {alert.acknowledged ? (
                      <Chip
                        label="Acknowledged"
                        color="success"
                        size="small"
                        icon={<CheckCircleIcon />}
                      />
                    ) : (
                      <Chip label="New" color="error" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      {!alert.acknowledged && (
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => handleAcknowledge(alert.id)}
                        >
                          Acknowledge
                        </Button>
                      )}
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(alert.id)}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
