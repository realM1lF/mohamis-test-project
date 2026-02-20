import React, { useState, useEffect } from 'react';
import KanbanBoard from './components/KanbanBoard';
import TicketDetail from './components/TicketDetail';
import NewTicketModal from './components/NewTicketModal';
import EditTicketModal from './components/EditTicketModal';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [editingTicket, setEditingTicket] = useState(null);
  const [showNewTicket, setShowNewTicket] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch tickets
  const fetchTickets = async () => {
    try {
      const response = await fetch(`${API_URL}/tickets`);
      const data = await response.json();
      setTickets(data);
    } catch (error) {
      console.error('Error fetching tickets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Poll every 3 seconds for updates
  useEffect(() => {
    fetchTickets();
    const interval = setInterval(fetchTickets, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTicketClick = (ticket) => {
    setSelectedTicket(ticket);
  };

  const handleTicketMove = async (ticketId, newStatus) => {
    try {
      const response = await fetch(`${API_URL}/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      
      if (response.ok) {
        // Optimistic update
        setTickets(prev => prev.map(t => 
          t.id === ticketId ? { ...t, status: newStatus } : t
        ));
        fetchTickets(); // Refresh from server
      }
    } catch (error) {
      console.error('Error moving ticket:', error);
    }
  };

  const handleCreateTicket = async (ticketData) => {
    try {
      const response = await fetch(`${API_URL}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ticketData),
      });
      if (response.ok) {
        fetchTickets();
        setShowNewTicket(false);
      }
    } catch (error) {
      console.error('Error creating ticket:', error);
    }
  };

  const handleUpdateTicket = async (ticketId, updates) => {
    try {
      const response = await fetch(`${API_URL}/tickets/${ticketId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      
      if (response.ok) {
        fetchTickets();
        setEditingTicket(null);
        // Also update selected ticket if open
        if (selectedTicket && selectedTicket.id === ticketId) {
          const updated = await response.json();
          setSelectedTicket(updated);
        }
      }
    } catch (error) {
      console.error('Error updating ticket:', error);
    }
  };

  const handleDeleteTicket = async (ticketId) => {
    if (!window.confirm('Ticket wirklich löschen?')) return;
    
    try {
      const response = await fetch(`${API_URL}/tickets/${ticketId}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        fetchTickets();
        setSelectedTicket(null);
        setEditingTicket(null);
      }
    } catch (error) {
      console.error('Error deleting ticket:', error);
    }
  };

  const handleAddComment = async (ticketId, content) => {
    try {
      await fetch(`${API_URL}/tickets/${ticketId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ author: 'user', content }),
      });
      // Refresh ticket details
      const response = await fetch(`${API_URL}/tickets/${ticketId}`);
      const updatedTicket = await response.json();
      setSelectedTicket(updatedTicket);
      fetchTickets();
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="App">
      <header className="app-header">
        <h1>🤖 KI-Mitarbeiter Board</h1>
        <button className="btn-primary" onClick={() => setShowNewTicket(true)}>
          + Neues Ticket
        </button>
      </header>

      <main className="app-main">
        <KanbanBoard 
          tickets={tickets} 
          onTicketClick={handleTicketClick}
          onTicketMove={handleTicketMove}
        />
      </main>

      {selectedTicket && (
        <TicketDetail
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onAddComment={handleAddComment}
          onEdit={() => {
            setEditingTicket(selectedTicket);
            setSelectedTicket(null);
          }}
          onDelete={() => handleDeleteTicket(selectedTicket.id)}
        />
      )}

      {showNewTicket && (
        <NewTicketModal
          onClose={() => setShowNewTicket(false)}
          onCreate={handleCreateTicket}
        />
      )}

      {editingTicket && (
        <EditTicketModal
          ticket={editingTicket}
          onClose={() => setEditingTicket(null)}
          onUpdate={handleUpdateTicket}
          onDelete={handleDeleteTicket}
        />
      )}
    </div>
  );
}

export default App;
