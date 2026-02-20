import React, { useState } from 'react';

function NewTicketModal({ onClose, onCreate }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    customer: 'test-customer',
    repository: 'realM1lF/personal-ki-agents',
    priority: 'medium',
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>🎫 Neues Ticket erstellen</h2>
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
              placeholder="z.B. Bug in Checkout fixen"
              required
            />
          </div>

          <div className="form-group">
            <label>Beschreibung:</label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Detaillierte Beschreibung des Problems oder der Anforderung..."
              required
            />
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

          <div className="form-group">
            <label>Priorität:</label>
            <select name="priority" value={formData.priority} onChange={handleChange}>
              <option value="low">Niedrig</option>
              <option value="medium">Mittel</option>
              <option value="high">Hoch</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button type="submit" className="btn-primary" style={{ flex: 1 }}>
              Ticket erstellen
            </button>
            <button type="button" onClick={onClose} style={{ 
              flex: 1, 
              padding: '0.75rem', 
              background: '#f3f4f6',
              border: '1px solid #ddd',
              borderRadius: '8px',
              cursor: 'pointer'
            }}>
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default NewTicketModal;
