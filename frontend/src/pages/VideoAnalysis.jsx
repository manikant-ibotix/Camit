import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { format } from 'date-fns';
import { analysisAPI } from '../services/api';
import { toast } from 'react-toastify';

export default function VideoAnalysis() {
  const [analyses, setAnalyses] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [crowdThreshold, setCrowdThreshold] = useState(10);
  const [frameSkip, setFrameSkip] = useState(3);
  const [viewDialog, setViewDialog] = useState(false);
  const [selectedAnalysis, setSelectedAnalysis] = useState(null);
  const [analysisDetails, setAnalysisDetails] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalyses();
    const interval = setInterval(loadAnalyses, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadAnalyses = async () => {
    try {
      const response = await analysisAPI.list();
      setAnalyses(response.data.analyses || []);
    } catch (error) {
      console.error('Error loading analyses:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a video file');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('crowd_threshold', crowdThreshold);
    formData.append('frame_skip', frameSkip);

    setUploading(true);
    setUploadProgress(0);

    try {
      const response = await analysisAPI.upload(formData, (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
      });

      toast.success('Video uploaded successfully! Analysis started.');
      setSelectedFile(null);
      setUploadProgress(0);
      loadAnalyses();
    } catch (error) {
      console.error('Error uploading video:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload video');
    } finally {
      setUploading(false);
    }
  };

  const handleViewResults = async (analysisId) => {
    setLoading(true);
    setViewDialog(true);
    setSelectedAnalysis(analysisId);

    try {
      const response = await analysisAPI.getStatistics(analysisId);
      setAnalysisDetails(response.data);
    } catch (error) {
      console.error('Error loading analysis details:', error);
      toast.error('Failed to load analysis details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (analysisId) => {
    if (window.confirm('Are you sure you want to delete this analysis?')) {
      try {
        await analysisAPI.delete(analysisId);
        toast.success('Analysis deleted successfully');
        loadAnalyses();
      } catch (error) {
        console.error('Error deleting analysis:', error);
        toast.error('Failed to delete analysis');
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'info';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDetectionColor = (type) => {
    switch (type) {
      case 'fall':
        return 'error';
      case 'lying':
        return 'warning';
      case 'pushing':
        return 'error';
      case 'crowd':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Video Analysis
      </Typography>

      {/* Upload Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload Video for Analysis
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <Button
              variant="outlined"
              component="label"
              fullWidth
              startIcon={<CloudUploadIcon />}
              disabled={uploading}
            >
              {selectedFile ? selectedFile.name : 'Select Video File'}
              <input
                type="file"
                hidden
                accept="video/mp4,video/avi,video/mov,video/mkv"
                onChange={handleFileSelect}
                disabled={uploading}
              />
            </Button>
          </Grid>
          <Grid item xs={6} md={2}>
            <TextField
              label="Crowd Threshold"
              type="number"
              value={crowdThreshold}
              onChange={(e) => setCrowdThreshold(parseInt(e.target.value) || 10)}
              fullWidth
              disabled={uploading}
              helperText="People count"
            />
          </Grid>
          <Grid item xs={6} md={2}>
            <TextField
              label="Frame Skip"
              type="number"
              value={frameSkip}
              onChange={(e) => setFrameSkip(parseInt(e.target.value) || 3)}
              fullWidth
              disabled={uploading}
              helperText="Process every Nth frame"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              fullWidth
              size="large"
            >
              {uploading ? 'Uploading...' : 'Upload & Analyze'}
            </Button>
          </Grid>
        </Grid>
        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="body2" color="textSecondary" align="center" sx={{ mt: 1 }}>
              Uploading: {uploadProgress}%
            </Typography>
          </Box>
        )}
        <Alert severity="info" sx={{ mt: 2 }}>
          Supported formats: MP4, AVI, MOV, MKV. Frame skip 1 = highest quality (slower), 5 = faster processing.
        </Alert>
      </Paper>

      {/* Analyses List */}
      <Paper>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Analysis History</Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Filename</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Total Detections</TableCell>
                <TableCell>Uploaded</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {analyses.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography color="textSecondary">
                      No analyses yet. Upload a video to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                analyses.map((analysis) => (
                  <TableRow key={analysis.analysis_id}>
                    <TableCell>{analysis.filename}</TableCell>
                    <TableCell>
                      {analysis.duration ? `${analysis.duration.toFixed(1)}s` : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={analysis.status}
                        color={getStatusColor(analysis.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{analysis.total_detections || 0}</TableCell>
                    <TableCell>
                      {analysis.created_at
                        ? format(new Date(analysis.created_at), 'MMM dd, yyyy HH:mm')
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleViewResults(analysis.analysis_id)}
                          disabled={analysis.status !== 'completed'}
                        >
                          <VisibilityIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(analysis.analysis_id)}
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
      </Paper>

      {/* Results Dialog */}
      <Dialog
        open={viewDialog}
        onClose={() => setViewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Analysis Results</DialogTitle>
        <DialogContent>
          {loading ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : analysisDetails ? (
            <Box>
              {/* Video Info */}
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                <Typography variant="subtitle2" color="textSecondary">
                  Video Information
                </Typography>
                <Typography variant="body2">
                  <strong>Filename:</strong> {analysisDetails.video_info?.filename}
                </Typography>
                <Typography variant="body2">
                  <strong>Duration:</strong> {analysisDetails.video_info?.duration?.toFixed(1)}s
                </Typography>
                <Typography variant="body2">
                  <strong>Resolution:</strong> {analysisDetails.video_info?.resolution}
                </Typography>
                <Typography variant="body2">
                  <strong>FPS:</strong> {analysisDetails.video_info?.fps?.toFixed(1)}
                </Typography>
              </Paper>

              {/* Statistics */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" variant="body2">
                        Falls
                      </Typography>
                      <Typography variant="h4" color="error.main">
                        {analysisDetails.statistics?.total_fall_detections || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" variant="body2">
                        Lying
                      </Typography>
                      <Typography variant="h4" color="warning.main">
                        {analysisDetails.statistics?.total_lying_detections || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" variant="body2">
                        Pushing
                      </Typography>
                      <Typography variant="h4" color="error.main">
                        {analysisDetails.statistics?.total_pushing_detections || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" variant="body2">
                        Crowd
                      </Typography>
                      <Typography variant="h4" color="info.main">
                        {analysisDetails.statistics?.total_crowd_detections || 0}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>

              {/* Timeline */}
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Detection Timeline (First 50 incidents)
              </Typography>
              {analysisDetails.timeline && analysisDetails.timeline.length > 0 ? (
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Time</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Confidence</TableCell>
                        <TableCell>Details</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analysisDetails.timeline.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{formatTime(item.timestamp)}</TableCell>
                          <TableCell>
                            <Chip
                              label={item.type.toUpperCase()}
                              color={getDetectionColor(item.type)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell>
                            {item.confidence ? `${(item.confidence * 100).toFixed(1)}%` : 'N/A'}
                          </TableCell>
                          <TableCell>
                            {item.person_count ? `${item.person_count} people` : 'Frame ' + item.frame}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="textSecondary" align="center" sx={{ py: 2 }}>
                  No incidents detected
                </Typography>
              )}
              {analysisDetails.total_incidents > 50 && (
                <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                  Showing 50 of {analysisDetails.total_incidents} total incidents
                </Typography>
              )}
            </Box>
          ) : (
            <Typography>No data available</Typography>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
