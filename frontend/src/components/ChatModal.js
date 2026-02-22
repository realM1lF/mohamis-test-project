import React, { useState, useEffect } from 'react';
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
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  CircularProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import SendIcon from '@mui/icons-material/Send';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const STORAGE_KEY = (agentId) => `chat_session_${agentId}`;

function ChatModal({ onClose }) {
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/config/agents`)
      .then((r) => r.json())
      .catch(() => [])
      .then((a) => {
        setAgents(a);
        if (a.length === 1) setSelectedAgent(a[0].id);
        setLoading(false);
      });
  }, []);

  // Beim Agent-Wechsel oder Öffnen: Session aus localStorage laden, Verlauf vom Backend holen
  useEffect(() => {
    if (!selectedAgent) return;
    const stored = localStorage.getItem(STORAGE_KEY(selectedAgent));
    if (stored) {
      setSessionId(stored);
      fetch(`${API_URL}/chat/history/${stored}`)
        .then((r) => r.json())
        .catch(() => ({ messages: [] }))
        .then((data) => setMessages(data.messages || []));
    } else {
      setSessionId(null);
      setMessages([]);
    }
  }, [selectedAgent]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || !selectedAgent) return;
    setSending(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: selectedAgent,
          message: inputText.trim(),
          session_id: sessionId,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || res.statusText);
      }
      const data = await res.json();
      const sid = data.session_id;
      setSessionId(sid);
      localStorage.setItem(STORAGE_KEY(selectedAgent), sid);
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: inputText.trim() },
        { role: 'assistant', content: data.reply },
      ]);
      setInputText('');
    } catch (err) {
      setError(err.message || 'Fehler beim Senden');
    } finally {
      setSending(false);
    }
  };

  const handleClear = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_URL}/chat/session/${sessionId}`, { method: 'DELETE' });
      } catch {
        /* ignore */
      }
    }
    if (selectedAgent) {
      localStorage.removeItem(STORAGE_KEY(selectedAgent));
    }
    setSessionId(null);
    setMessages([]);
    setError(null);
  };

  const agentName = agents.find((a) => a.id === selectedAgent)?.name || selectedAgent;

  if (loading) {
    return (
      <Dialog open onClose={onClose} maxWidth="sm" fullWidth
        PaperProps={{ sx: { borderRadius: 4, backgroundColor: '#FDFCFF' } }}>
        <DialogContent sx={{ display: 'flex', justifyContent: 'center', py: 6 }}>
          <CircularProgress />
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog
      open
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 4,
          backgroundColor: '#FDFCFF',
          maxHeight: '90vh',
        },
      }}
    >
      <DialogTitle
        sx={{
          px: 3,
          py: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #DDE3EA',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2,
              backgroundColor: '#EBDDFF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SmartToyIcon sx={{ color: '#65587B', fontSize: 22 }} />
          </Box>
          <Box>
            <Typography variant="titleMedium" sx={{ color: '#1A1C1E', fontWeight: 600 }}>
              Chat mit KI-Mitarbeiter
            </Typography>
            <FormControl size="small" sx={{ mt: 0.5, minWidth: 140 }}>
              <InputLabel sx={{ color: '#72787E' }}>Agent</InputLabel>
              <Select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                label="Agent"
                sx={{
                  borderRadius: 2,
                  backgroundColor: '#F2F4F7',
                  '& fieldset': { borderColor: 'transparent' },
                }}
              >
                {agents.map((a) => (
                  <MenuItem key={a.id} value={a.id}>
                    {a.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {messages.length > 0 && (
            <IconButton
              onClick={handleClear}
              size="small"
              title="Chat-Verlauf löschen"
              sx={{ color: '#72787E', '&:hover': { color: '#DC2626' } }}
            >
              <DeleteSweepIcon />
            </IconButton>
          )}
          <IconButton onClick={onClose} size="small" sx={{ color: '#72787E' }}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0, display: 'flex', flexDirection: 'column', minHeight: 320 }}>
        <List
          sx={{
            flex: 1,
            overflow: 'auto',
            py: 2,
            px: 2,
          }}
        >
          {messages.length === 0 && (
            <ListItem>
              <ListItemText
                primary={
                  <Typography variant="bodyMedium" sx={{ color: '#72787E', fontStyle: 'italic' }}>
                    Wähle einen Agent und schreibe eine Nachricht …
                  </Typography>
                }
              />
            </ListItem>
          )}
          {messages.map((m, i) => (
            <ListItem
              key={i}
              alignItems="flex-start"
              sx={{
                px: 1.5,
                py: 1.5,
                borderRadius: 3,
                backgroundColor: m.role === 'assistant' ? '#EBDDFF' : '#F2F4F7',
                mb: 1,
              }}
            >
              <ListItemAvatar>
                <Avatar
                  sx={{
                    bgcolor: m.role === 'assistant' ? '#65587B' : '#006495',
                    width: 32,
                    height: 32,
                  }}
                >
                  {m.role === 'assistant' ? (
                    <SmartToyIcon sx={{ fontSize: 16 }} />
                  ) : (
                    <PersonIcon sx={{ fontSize: 16 }} />
                  )}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Typography variant="labelMedium" sx={{ color: '#41474D', fontWeight: 600, mb: 0.5 }}>
                    {m.role === 'assistant' ? agentName : 'Du'}
                  </Typography>
                }
                secondary={
                  <Typography
                    variant="bodyMedium"
                    sx={{ color: '#1A1C1E', whiteSpace: 'pre-wrap', mt: 0.5 }}
                  >
                    {m.content}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>

        {error && (
          <Box sx={{ px: 2, pb: 1 }}>
            <Typography variant="bodySmall" sx={{ color: '#DC2626' }}>
              {error}
            </Typography>
          </Box>
        )}

        <Box
          component="form"
          onSubmit={handleSend}
          sx={{
            p: 2,
            borderTop: '1px solid #DDE3EA',
            display: 'flex',
            gap: 1,
            alignItems: 'flex-start',
          }}
        >
          <TextField
            fullWidth
            placeholder={`Nachricht an ${agentName || 'Agent'}…`}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            variant="outlined"
            size="small"
            multiline
            maxRows={3}
            disabled={!selectedAgent || sending}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                backgroundColor: '#F2F4F7',
                '& fieldset': { borderColor: 'transparent' },
                '&:hover fieldset': { borderColor: '#C1C7CE' },
                '&.Mui-focused fieldset': { borderColor: '#006495' },
              },
            }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={!inputText.trim() || !selectedAgent || sending}
            sx={{
              minWidth: 48,
              height: 48,
              borderRadius: 3,
              backgroundColor: '#006495',
              '&:hover': { backgroundColor: '#004B6F' },
              '&.Mui-disabled': { backgroundColor: '#DDE3EA' },
            }}
          >
            {sending ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
          </Button>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2, borderTop: '1px solid #DDE3EA', justifyContent: 'space-between' }}>
        <Button
          startIcon={<DeleteSweepIcon />}
          onClick={handleClear}
          disabled={messages.length === 0}
          sx={{
            color: '#72787E',
            textTransform: 'none',
            borderRadius: 5,
            '&:hover': { color: '#DC2626' },
            '&.Mui-disabled': { color: '#C1C7CE' },
          }}
        >
          Verlauf löschen
        </Button>
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

export default ChatModal;
