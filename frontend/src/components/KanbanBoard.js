import React, { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCorners,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const COLUMNS = [
  { id: 'backlog', title: '📥 Backlog', color: '#667eea' },
  { id: 'in_progress', title: '🔨 In Progress', color: '#f59e0b' },
  { id: 'clarification', title: '❓ Rückfrage', color: '#ef4444' },
  { id: 'testing', title: '🧪 Testing', color: '#10b981' },
  { id: 'done', title: '✅ Done', color: '#6b7280' },
];

// Sortable Ticket Card Component
function SortableTicketCard({ ticket, onClick }) {
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

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', { 
      day: '2-digit', 
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`ticket-card ${ticket.status}`}
      onClick={(e) => {
        if (!isDragging) onClick(ticket);
      }}
    >
      <span className={`ticket-priority priority-${ticket.priority}`}>
        {ticket.priority}
      </span>
      <div className="ticket-title">{ticket.title}</div>
      <div className="ticket-meta">
        <span>{ticket.customer}</span>
        <span>{formatDate(ticket.created_at)}</span>
      </div>
      {ticket.agent && (
        <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#10b981' }}>
          🤖 {ticket.agent === 'mohami' ? 'Mohami' : ticket.agent}
        </div>
      )}
    </div>
  );
}

// Droppable Column Component
function DroppableColumn({ column, tickets, onTicketClick, isOver }) {
  const { setNodeRef } = useSortable({
    id: column.id,
    data: {
      type: 'column',
      column,
    },
  });

  const ticketIds = tickets.map(t => t.id);

  return (
    <div 
      ref={setNodeRef}
      className={`kanban-column ${isOver ? 'drag-over' : ''}`}
      data-column={column.id}
    >
      <div className="column-header" style={{ borderColor: column.color }}>
        <h3>{column.title}</h3>
        <span className="ticket-count">{tickets.length}</span>
      </div>
      
      <SortableContext
        items={ticketIds}
        strategy={verticalListSortingStrategy}
      >
        <div className="column-content">
          {tickets.map(ticket => (
            <SortableTicketCard
              key={ticket.id}
              ticket={ticket}
              onClick={onTicketClick}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  );
}

function KanbanBoard({ tickets, onTicketClick, onTicketMove }) {
  const [activeId, setActiveId] = useState(null);
  const [overColumn, setOverColumn] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: (event) => {
        const { active } = event;
        return active?.rect?.current?.translated;
      },
    })
  );

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragOver = (event) => {
    const { over } = event;
    
    if (over) {
      // Check if hovering over a column
      const overColumnId = over.data?.current?.column?.id || over.id;
      if (COLUMNS.find(c => c.id === overColumnId)) {
        setOverColumn(overColumnId);
      }
    }
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    
    setActiveId(null);
    setOverColumn(null);

    if (!over) return;

    const ticketId = active.id;
    
    // Determine target column
    let targetColumnId;
    
    // Check if dropped over a column directly
    if (over.data?.current?.type === 'column') {
      targetColumnId = over.data.current.column.id;
    } else if (over.data?.current?.type === 'ticket') {
      // Dropped over a ticket - get its column
      targetColumnId = over.data.current.ticket.status;
    } else {
      // Check if over.id is a column id
      targetColumnId = over.id;
    }

    // Validate column
    if (!COLUMNS.find(c => c.id === targetColumnId)) {
      return;
    }

    // Find the ticket
    const ticket = tickets.find(t => t.id === ticketId);
    if (!ticket) return;

    // Only move if status changed
    if (ticket.status !== targetColumnId) {
      console.log(`Moving ticket ${ticketId} from ${ticket.status} to ${targetColumnId}`);
      onTicketMove(ticketId, targetColumnId);
    }
  };

  const activeTicket = activeId ? tickets.find(t => t.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
    >
      <div className="kanban-board">
        {COLUMNS.map(column => {
          const columnTickets = tickets.filter(t => t.status === column.id);
          
          return (
            <DroppableColumn
              key={column.id}
              column={column}
              tickets={columnTickets}
              onTicketClick={onTicketClick}
              isOver={overColumn === column.id}
            />
          );
        })}
      </div>

      <DragOverlay>
        {activeTicket ? (
          <div 
            className={`ticket-card ${activeTicket.status}`}
            style={{ 
              cursor: 'grabbing',
              boxShadow: '0 8px 20px rgba(0,0,0,0.2)',
              transform: 'rotate(3deg)',
            }}
          >
            <span className={`ticket-priority priority-${activeTicket.priority}`}>
              {activeTicket.priority}
            </span>
            <div className="ticket-title">{activeTicket.title}</div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}

export default KanbanBoard;
