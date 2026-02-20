import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function TicketDetail({ ticket, onClose, onAddComment, onEdit, onDelete }) {
  const [ticketDetails, setTicketDetails] = useState(null);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTicketDetails();
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

  const getStatusLabel = (status) => {
    const labels = {
      backlog: '📥 Backlog',
      in_progress: '🔨 In Progress',
      clarification: '❓ Rückfrage',
      testing: '🧪 Testing',
      done: '✅ Done',
    };
    return labels[status] || status;
  };

  if (loading) return (
    <div className="modal-overlay">
      <div className="modal-content">Loading...</div>
    </div>
  );

  const details = ticketDetails || ticket;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🎫 {details.title}</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="ticket-info">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <p><strong>ID:</strong> {details.id}</p>
            <p><strong>Status:</strong> {getStatusLabel(details.status)}</p>
            <p><strong>Priorität:</strong> {details.priority}</p>
            <p><strong>Kunde:</strong> {details.customer}</p>
          </div>
          <p><strong>Repository:</strong> {details.repository}</p>
          {details.agent && <p><strong>Agent:</strong> 🤖 {details.agent === 'mohami' ? 'Mohami' : details.agent}</p>}
          <p><strong>Erstellt:</strong> {formatDate(details.created_at)}</p>
          <p><strong>Aktualisiert:</strong> {formatDate(details.updated_at)}</p>
        </div>

        <div className="form-group" style={{ marginTop: '1rem' }}>
          <label>Beschreibung:</label>
          <div style={{ 
            background: '#f9fafb', 
            padding: '1rem', 
            borderRadius: '8px',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6'
          }}>
            {details.description}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <button 
            onClick={onEdit}
            className="btn-primary"
            style={{ flex: 1 }}
          >
            ✏️ Bearbeiten
          </button>
          <button 
            onClick={onDelete}
            style={{ 
              flex: 1,
              padding: '0.75rem',
              background: '#ef4444',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            🗑️ Löschen
          </button>
        </div>

        <div className="comments-section">
          <h3>💬 Kommunikation ({details.comments?.length || 0})</h3>
          
          {details.comments?.map(comment => (
            <div key={comment.id} className="comment">
              <div className="comment-header">
                <span className={`comment-author ${comment.author.startsWith('dev-') ? 'agent' : ''}`}>
                  {comment.author === 'mohami' ? '🤖 Mohami' : '👤 ' + comment.author}
                  {comment.author === 'mohami' && <span className="agent-badge">KI</span>}
                </span>
                <span className="comment-time">{formatDate(comment.created_at)}</span>
              </div>
              <div className="comment-content">{comment.content}</div>
            </div>
          ))}

          <form onSubmit={handleSubmitComment} className="comment-form">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Antwort an Mohami..."
            />
            <button type="submit">Senden</button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default TicketDetail;
