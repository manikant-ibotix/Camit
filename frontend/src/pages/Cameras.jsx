import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Chip,
  Grid,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import { cameraAPI } from '../services/api';
import { toast } from 'react-toastify';

export default function Cameras() {
  const [cameras, setCameras] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCamera, setEditingCamera] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    ip_address: '',
    rtsp_url: '',
    username: '',
    password: '',
    crowd_threshold: 10,
    enabled: true,
  });

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      const response = await cameraAPI.getAll();
      setCameras(response.data);
    } catch (error) {
      console.error('Error loading cameras:', error);
      toast.error('Failed to load cameras');
    }
  };

  const handleOpenDialog = (camera = null) => {
    if (camera) {
      setEditingCamera(camera);
      setFormData({
        name: camera.name,
        location: camera.location || '',
        ip_address: camera.ip_address,
        rtsp_url: camera.rtsp_url,
        username: camera.username || '',
        password: camera.password || '',
        crowd_threshold: camera.crowd_threshold,
        enabled: camera.enabled,
      });
    } else {
      setEditingCamera(null);
      setFormData({
        name: '',
        location: '',
        ip_address: '',
        rtsp_url: '',
        username: '',
        password: '',
        crowd_threshold: 10,
        enabled: true,
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCamera(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingCamera) {
        await cameraAPI.update(editingCamera.id, formData);
        toast.success('Camera updated successfully');
      } else {
        await cameraAPI.create(formData);
        toast.success('Camera created successfully');
      }
      handleCloseDialog();
      loadCameras();
    } catch (error) {
      console.error('Error saving camera:', error);
      toast.error(error.response?.data?.detail || 'Failed to save camera');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this camera?')) {
      try {
        await cameraAPI.delete(id);
        toast.success('Camera deleted successfully');
        loadCameras();
      } catch (error) {
        console.error('Error deleting camera:', error);
        toast.error('Failed to delete camera');
      }
    }
  };

  const handleStart = async (id) => {
    try {
      await cameraAPI.start(id);
      toast.success('Camera started');
      loadCameras();
    } catch (error) {
      console.error('Error starting camera:', error);
      toast.error('Failed to start camera');
    }
  };

  const handleStop = async (id) => {
    try {
      await cameraAPI.stop(id);
      toast.success('Camera stopped');
      loadCameras();
    } catch (error) {
      console.error('Error stopping camera:', error);
      toast.error('Failed to stop camera');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'error':
        return 'error';
      case 'connecting':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Cameras</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Camera
        </Button>
      </Box>

      <Grid container spacing={3}>
        {cameras.map((camera) => (
          <Grid item xs={12} md={6} lg={4} key={camera.id}>
            <Paper sx={{ p: 2 }}>
              <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                <Box>
                  <Typography variant="h6">{camera.name}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {camera.location || 'No location'}
                  </Typography>
                </Box>
                <Chip
                  label={camera.status}
                  color={getStatusColor(camera.status)}
                  size="small"
                />
              </Box>

              <Box mb={2}>
                <Typography variant="body2" color="textSecondary">
                  IP: {camera.ip_address}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Crowd Threshold: {camera.crowd_threshold} people
                </Typography>
              </Box>

              <Box display="flex" gap={1}>
                {camera.status === 'active' ? (
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleStop(camera.id)}
                    title="Stop"
                  >
                    <StopIcon />
                  </IconButton>
                ) : (
                  <IconButton
                    size="small"
                    color="success"
                    onClick={() => handleStart(camera.id)}
                    title="Start"
                  >
                    <PlayArrowIcon />
                  </IconButton>
                )}
                <IconButton
                  size="small"
                  color="primary"
                  onClick={() => handleOpenDialog(camera)}
                  title="Edit"
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => handleDelete(camera.id)}
                  title="Delete"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {cameras.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No cameras configured. Click "Add Camera" to get started.
          </Typography>
        </Paper>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingCamera ? 'Edit Camera' : 'Add Camera'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Camera Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              fullWidth
            />
            <TextField
              label="IP Address"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              required
              fullWidth
              placeholder="192.168.1.100"
            />
            <TextField
              label="RTSP URL"
              value={formData.rtsp_url}
              onChange={(e) => setFormData({ ...formData, rtsp_url: e.target.value })}
              required
              fullWidth
              placeholder="rtsp://username:password@192.168.1.100:554/stream1"
            />
            <TextField
              label="Username (Optional)"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              fullWidth
            />
            <TextField
              label="Password (Optional)"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              type="password"
              fullWidth
            />
            <TextField
              label="Crowd Threshold"
              value={formData.crowd_threshold}
              onChange={(e) =>
                setFormData({ ...formData, crowd_threshold: parseInt(e.target.value) || 10 })
              }
              type="number"
              fullWidth
              helperText="Number of people to trigger crowd alert"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingCamera ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
