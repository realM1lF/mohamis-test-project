import React from 'react';
import { Card, CardContent, Typography, Chip, Box, Avatar } from '@mui/material';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import { priorityColors, statusColors } from '../theme';

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('de-DE', { 
    day: '2-digit', 
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getPriorityColor = (priority) => {
  return priorityColors[priority] || priorityColors.medium;
};

const getStatusColor = (status) => {
  return statusColors[status] || statusColors.backlog;
};

function TicketCard({ ticket, onClick }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: ticket.id,
    data: {
      type: 'ticket',
      ticket,
    }
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const priorityColor = getPriorityColor(ticket.priority);
  const statusColor = getStatusColor(ticket.status);

  return (
    <Card
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      onClick={(e) => {
        if (!isDragging) onClick(ticket);
      }}
      sx={{
        ...style,
        mb: 1.5,
        cursor: isDragging ? 'grabbing' : 'grab',
        borderLeft: `4px solid ${statusColor.main}`,
        backgroundColor: '#FDFCFF',
        '&:hover': {
          transform: isDragging ? 'none' : 'translateY(-2px)',
        },
        userSelect: 'none',
        touchAction: 'none',
      }}
      elevation={isDragging ? 4 : 1}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* Priority Chip */}
        <Chip
          label={ticket.priority.toUpperCase()}
          size="small"
          sx={{
            mb: 1,
            backgroundColor: priorityColor.container,
            color: priorityColor.onContainer,
            fontWeight: 600,
            fontSize: '0.625rem',
            height: 20,
          }}
        />
        
        {/* Title */}
        <Typography 
          variant="titleMedium" 
          sx={{ 
            mb: 1, 
            display: 'block',
            lineHeight: 1.4,
            color: '#1A1C1E',
          }}
        >
          {ticket.title}
        </Typography>
        
        {/* Meta Info */}
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          mt: 1,
        }}>
          <Typography 
            variant="bodySmall" 
            sx={{ color: '#72787E' }}
          >
            {ticket.customer}
          </Typography>
          <Typography 
            variant="labelSmall" 
            sx={{ color: '#72787E' }}
          >
            {formatDate(ticket.created_at)}
          </Typography>
        </Box>
        
        {/* Agent Assignment */}
        {ticket.agent && (
          <Box sx={{ 
            mt: 1.5, 
            display: 'flex', 
            alignItems: 'center', 
            gap: 0.5,
            backgroundColor: '#ECEEF1',
            p: 0.5,
            borderRadius: 2,
            width: 'fit-content',
          }}>
            <Avatar 
              sx={{ 
                width: 20, 
                height: 20, 
                bgcolor: '#006495',
                fontSize: '0.75rem',
              }}
            >
              {ticket.agent === 'mohami' ? (
                <SmartToyIcon sx={{ fontSize: 14 }} />
              ) : (
                <PersonIcon sx={{ fontSize: 14 }} />
              )}
            </Avatar>
            <Typography 
              variant="labelSmall" 
              sx={{ 
                color: '#006495',
                fontWeight: 500,
                pr: 0.5,
              }}
            >
              {ticket.agent === 'mohami' ? 'Mohami' : ticket.agent}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default TicketCard;
