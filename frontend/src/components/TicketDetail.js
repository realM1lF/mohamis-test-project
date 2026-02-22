import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  TextField,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Divider,
  IconButton,
  Grid,
  Paper,
  CircularProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import SendIcon from '@mui/icons-material/Send';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { statusColors, priorityColors } from '../theme';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const STATUS_LABELS = {
  backlog: 'Backlog',
  in_progress: 'In Progress',
  clarification: 'Rückfrage',
  testing: 'Testing',
  done: 'Done',
};

const STATUS_ICONS = {
  backlog: 'inbox',
  in_progress: 'engineering',
  clarification: 'help',
  testing: 'science',
  done: 'check_circle',
};

function TicketDetail({ ticket, onClose, onAddComment, onEdit, onDelete }) {
  const [ticketDetails, setTicketDetails] = useState(null);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTicketDetails();
    const interval = setInterval(fetchTicketDetails, 3000);
    return () => clearInterval(interval);
  }, [ticket.id]);

  const fetchTicketDetails = async () => {
    try {
      const response = await fetch(`${API_URL}/tickets/${ticket.id}`);
      const data = await response.json();
      setTicketDetails(data);
    } catch (error) {
      console.error('Error fetching ticket details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    onAddComment(ticket.id, newComment);
    setNewComment('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('de-DE');
  };

  const details = ticketDetails || ticket;
  const statusColor = statusColors[details.status] || statusColors.backlog;
  const priorityColor = priorityColors[details.priority] || priorityColors.medium;
  const isAgentWorking = Boolean(details.agent_working_since);

  return (
    <Dialog
      open={true}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 4,
          backgroundColor: '#FDFCFF',
          maxHeight: '90vh',
        },
      }}
    >
      {/* Dialog Header */}
      <DialogTitle sx={{ 
        px: 3, 
        py: 2.5,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #DDE3EA',
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              backgroundColor: statusColor.container,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span 
              className="material-symbols-rounded" 
              style={{ color: statusColor.main, fontSize: 20 }}
            >
              {STATUS_ICONS[ticket.status] || 'task'}
            </span>
          </Box>
          <Typography 
            variant="headlineSmall" 
            sx={{ 
              color: '#1A1C1E',
              fontWeight: 500,
            }}
          >
            {details.title}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small" sx={{ color: '#72787E' }}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ px: 3, py: 3, backgroundColor: '#FDFCFF' }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <Typography color="text.secondary">Laden...</Typography>
          </Box>
        ) : (
          <>
            {/* Status & Priority Chips */}
            <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
              <Chip
                icon={<span className="material-symbols-rounded" style={{ fontSize: 16 }}>
                  {STATUS_ICONS[details.status]}
                </span>}
                label={STATUS_LABELS[details.status] || details.status}
                sx={{
                  backgroundColor: statusColor.container,
                  color: statusColor.onContainer,
                  fontWeight: 500,
                  '& .MuiChip-icon': {
                    color: statusColor.onContainer,
                  },
                }}
              />
              <Chip
                label={details.priority.toUpperCase()}
                sx={{
                  backgroundColor: priorityColor.container,
                  color: priorityColor.onContainer,
                  fontWeight: 600,
                }}
              />
              {details.agent && (
                <Chip
                  icon={<SmartToyIcon sx={{ fontSize: 16 }} />}
                  label={details.agent === 'mohami' ? 'Mohami' : details.agent}
                  sx={{
                    backgroundColor: '#EBDDFF',
                    color: '#211634',
                    fontWeight: 500,
                    '& .MuiChip-icon': {
                      color: '#65587B',
                    },
                  }}
                />
              )}
              {isAgentWorking && (
                <Chip
                  icon={<CircularProgress size={14} thickness={7} sx={{ color: '#006495 !important' }} />}
                  label="Agent arbeitet..."
                  sx={{
                    backgroundColor: '#CBE6FF',
                    color: '#00344F',
                    fontWeight: 600,
                    '& .MuiChip-icon': {
                      color: '#006495',
                    },
                  }}
                />
              )}
            </Box>

            {/* Ticket Info Grid */}
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} sm={6}>
                <Typography variant="labelMedium" sx={{ color: '#72787E', mb: 0.5, display: 'block' }}>
                  ID
                </Typography>
                <Typography variant="bodyMedium" sx={{ color: '#1A1C1E' }}>
                  #{details.id}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="labelMedium" sx={{ color: '#72787E', mb: 0.5, display: 'block' }}>
                  Kunde
                </Typography>
                <Typography variant="bodyMedium" sx={{ color: '#1A1C1E' }}>
                  {details.customer}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="labelMedium" sx={{ color: '#72787E', mb: 0.5, display: 'block' }}>
                  Repository
                </Typography>
                <Typography variant="bodyMedium" sx={{ color: '#1A1C1E' }}>
                  {details.repository}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="labelMedium" sx={{ color: '#72787E', mb: 0.5, display: 'block' }}>
                  Erstellt
                </Typography>
                <Typography variant="bodyMedium" sx={{ color: '#1A1C1E' }}>
                  {formatDate(details.created_at)}
                </Typography>
              </Grid>
            </Grid>

            {/* Description */}
            <Paper
              elevation={0}
              sx={{
                p: 2.5,
                backgroundColor: '#F2F4F7',
                borderRadius: 3,
                mb: 3,
              }}
            >
              <Typography 
                variant="labelMedium" 
                sx={{ color: '#72787E', mb: 1, display: 'block' }}
              >
                Beschreibung
              </Typography>
              <Typography 
                variant="bodyMedium" 
                sx={{ 
                  color: '#1A1C1E',
                  whiteSpace: 'pre-wrap',
                  lineHeight: 1.6,
                }}
              >
                {details.description}
              </Typography>
            </Paper>

            {/* Actions */}
            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              <Button
                variant="outlined"
                startIcon={<EditIcon />}
                onClick={onEdit}
                sx={{
                  borderColor: '#006495',
                  color: '#006495',
                  borderRadius: 5,
                  textTransform: 'none',
                  '&:hover': {
                    backgroundColor: '#CBE6FF',
                    borderColor: '#006495',
                  },
                }}
              >
                Bearbeiten
              </Button>
              <Button
                variant="outlined"
                startIcon={<DeleteIcon />}
                onClick={onDelete}
                sx={{
                  borderColor: '#DC2626',
                  color: '#DC2626',
                  borderRadius: 5,
                  textTransform: 'none',
                  '&:hover': {
                    backgroundColor: '#FEE2E2',
                    borderColor: '#DC2626',
                  },
                }}
              >
                Löschen
              </Button>
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Comments Section */}
            <Box>
              <Typography 
                variant="titleMedium" 
                sx={{ 
                  color: '#1A1C1E',
                  mb: 2,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                }}
              >
                <span className="material-symbols-rounded" style={{ color: '#72787E' }}>
                  chat
                </span>
                Kommunikation ({details.comments?.length || 0})
              </Typography>

              {/* Comments List */}
              <List sx={{ mb: 2 }}>
                {details.comments?.map((comment, index) => (
                  <React.Fragment key={comment.id}>
                    <ListItem
                      alignItems="flex-start"
                      sx={{
                        px: 1.5,
                        py: 1.5,
                        borderRadius: 3,
                        backgroundColor: comment.author === 'mohami' ? '#EBDDFF' : '#F2F4F7',
                        mb: 1,
                      }}
                    >
                      <ListItemAvatar>
                        <Avatar
                          sx={{
                            bgcolor: comment.author === 'mohami' ? '#65587B' : '#006495',
                            width: 36,
                            height: 36,
                          }}
                        >
                          {comment.author === 'mohami' ? (
                            <SmartToyIcon sx={{ fontSize: 18 }} />
                          ) : (
                            <PersonIcon sx={{ fontSize: 18 }} />
                          )}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                            <Typography
                              variant="labelLarge"
                              sx={{
                                color: comment.author === 'mohami' ? '#211634' : '#001E30',
                                fontWeight: 600,
                              }}
                            >
                              {comment.author === 'mohami' ? 'Mohami' : comment.author}
                            </Typography>
                            {comment.author === 'mohami' && (
                              <Chip
                                label="KI"
                                size="small"
                                sx={{
                                  height: 18,
                                  fontSize: '0.625rem',
                                  backgroundColor: '#65587B',
                                  color: 'white',
                                  fontWeight: 600,
                                }}
                              />
                            )}
                            <Typography
                              variant="bodySmall"
                              sx={{ color: '#72787E', ml: 'auto' }}
                            >
                              {formatDate(comment.created_at)}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5, color: '#1A1C1E', '& p': { margin: '0 0 0.5em 0' }, '& ul': { margin: '0.25em 0', paddingLeft: 2 }, '& li': { marginBottom: 0.25 }, '& strong': { fontWeight: 700 }, '& code': { fontFamily: 'monospace', fontSize: '0.9em', backgroundColor: '#ECEEF1', px: 0.5, borderRadius: 1 } }}>
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {comment.content}
                            </ReactMarkdown>
                          </Box>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>

              {/* Comment Form */}
              <Box 
                component="form" 
                onSubmit={handleSubmitComment}
                sx={{ 
                  display: 'flex', 
                  gap: 1, 
                  alignItems: 'flex-start',
                  mt: 2,
                }}
              >
                <TextField
                  fullWidth
                  placeholder="Antwort an Mohami..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  variant="outlined"
                  size="small"
                  multiline
                  maxRows={3}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 3,
                      backgroundColor: '#F2F4F7',
                      '& fieldset': {
                        borderColor: 'transparent',
                      },
                      '&:hover fieldset': {
                        borderColor: '#C1C7CE',
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: '#006495',
                      },
                    },
                  }}
                />
                <Button
                  type="submit"
                  variant="contained"
                  disabled={!newComment.trim()}
                  sx={{
                    minWidth: 48,
                    height: 48,
                    borderRadius: 3,
                    backgroundColor: '#006495',
                    '&:hover': {
                      backgroundColor: '#004B6F',
                    },
                    '&.Mui-disabled': {
                      backgroundColor: '#DDE3EA',
                    },
                  }}
                >
                  <SendIcon />
                </Button>
              </Box>
            </Box>
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #DDE3EA' }}>
        <Button 
          onClick={onClose}
          sx={{
            color: '#72787E',
            textTransform: 'none',
            borderRadius: 5,
            px: 3,
          }}
        >
          Schließen
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default TicketDetail;
