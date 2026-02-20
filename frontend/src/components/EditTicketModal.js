import React, { useState } from 'react';

const STATUS_OPTIONS = [
  { value: 'backlog', label: '📥 Backlog' },
  { value: 'in_progress', label: '🔨 In Progress' },
  { value: 'clarification', label: '❓ Rückfrage' },
  { value: 'testing', label: '🧪 Testing' },
  { value: 'done', label: '✅ Done' },
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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✏️ Ticket bearbeiten</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Titel:</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Beschreibung:</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={6}
              required
            />
          </div>

          <div className="form-group">
            <label>Status:</label>
            <select name="status" value={formData.status} onChange={handleChange}>
              {STATUS_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Priorität:</label>
            <select name="priority" value={formData.priority} onChange={handleChange}>
              {PRIORITY_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Kunde:</label>
            <input
              type="text"
              name="customer"
              value={formData.customer}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Repository:</label>
            <input
              type="text"
              name="repository"
              value={formData.repository}
              onChange={handleChange}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button type="submit" className="btn-primary" style={{ flex: 1 }}>
              💾 Speichern
            </button>
            <button 
              type="button" 
              onClick={() => onDelete(ticket.id)}
              style={{ 
                padding: '0.75rem 1.5rem',
                background: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              🗑️ Löschen
            </button>
            <button 
              type="button" 
              onClick={onClose}
              style={{ 
                padding: '0.75rem 1.5rem',
                background: '#f3f4f6',
                border: '1px solid #ddd',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default EditTicketModal;
