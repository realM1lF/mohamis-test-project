import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  IconButton,
  Grid,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';

const STATUS_OPTIONS = [
  { value: 'backlog', label: 'Backlog' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'clarification', label: 'Rückfrage' },
  { value: 'testing', label: 'Testing' },
  { value: 'done', label: 'Done' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Niedrig' },
  { value: 'medium', label: 'Mittel' },
  { value: 'high', label: 'Hoch' },
];

function EditTicketModal({ ticket, onClose, onUpdate, onDelete }) {
  const [formData, setFormData] = useState({
    title: ticket.title,
    description: ticket.description,
    status: ticket.status,
    priority: ticket.priority,
    customer: ticket.customer,
    repository: ticket.repository,
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onUpdate(ticket.id, formData);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleDelete = () => {
    onDelete(ticket.id);
  };

  const isValid = formData.title.trim() && formData.description.trim();

  return (
    <Dialog
      open={true}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 4,
          backgroundColor: '#FDFCFF',
        },
      }}
    >
      <form onSubmit={handleSubmit}>
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
                backgroundColor: '#CBE6FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <EditIcon sx={{ color: '#006495', fontSize: 20 }} />
            </Box>
            <Typography 
              variant="headlineSmall" 
              sx={{ 
                color: '#1A1C1E',
                fontWeight: 500,
              }}
            >
              Ticket bearbeiten
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small" sx={{ color: '#72787E' }}>
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent sx={{ px: 3, py: 3 }}>
          <Grid container spacing={2.5}>
            {/* Title */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Titel"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
                  '& .MuiInputLabel-root': {
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  },
                }}
              />
            </Grid>

            {/* Description */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Beschreibung"
                name="description"
                value={formData.description}
                onChange={handleChange}
                required
                multiline
                rows={4}
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
                  '& .MuiInputLabel-root': {
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  },
                }}
              />
            </Grid>

            {/* Status & Priority */}
            <Grid item xs={12} sm={6}>
              <FormControl 
                fullWidth
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
              >
                <InputLabel 
                  id="status-label"
                  sx={{
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  }}
                >
                  Status
                </InputLabel>
                <Select
                  labelId="status-label"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  label="Status"
                >
                  {STATUS_OPTIONS.map(opt => (
                    <MenuItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl 
                fullWidth
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
              >
                <InputLabel 
                  id="priority-label"
                  sx={{
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  }}
                >
                  Priorität
                </InputLabel>
                <Select
                  labelId="priority-label"
                  name="priority"
                  value={formData.priority}
                  onChange={handleChange}
                  label="Priorität"
                >
                  {PRIORITY_OPTIONS.map(opt => (
                    <MenuItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Customer */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Kunde"
                name="customer"
                value={formData.customer}
                onChange={handleChange}
                required
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
                  '& .MuiInputLabel-root': {
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  },
                }}
              />
            </Grid>

            {/* Repository */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Repository"
                name="repository"
                value={formData.repository}
                onChange={handleChange}
                required
                variant="outlined"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
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
                  '& .MuiInputLabel-root': {
                    color: '#72787E',
                    '&.Mui-focused': {
                      color: '#006495',
                    },
                  },
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions 
          sx={{ 
            px: 3, 
            py: 2.5, 
            borderTop: '1px solid #DDE3EA', 
            gap: 1,
            justifyContent: 'space-between',
          }}
        >
          <Button
            type="button"
            variant="outlined"
            startIcon={<DeleteIcon />}
            onClick={handleDelete}
            sx={{
              borderColor: '#DC2626',
              color: '#DC2626',
              textTransform: 'none',
              borderRadius: 5,
              '&:hover': {
                backgroundColor: '#FEE2E2',
                borderColor: '#DC2626',
              },
            }}
          >
            Löschen
          </Button>
          
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              type="button"
              onClick={onClose}
              sx={{
                color: '#72787E',
                textTransform: 'none',
                borderRadius: 5,
                px: 3,
              }}
            >
              Abbrechen
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={<SaveIcon />}
              disabled={!isValid}
              sx={{
                backgroundColor: '#006495',
                textTransform: 'none',
                borderRadius: 5,
                px: 3,
                '&:hover': {
                  backgroundColor: '#004B6F',
                },
                '&.Mui-disabled': {
                  backgroundColor: '#DDE3EA',
                  color: '#72787E',
                },
              }}
            >
              Speichern
            </Button>
          </Box>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default EditTicketModal;
