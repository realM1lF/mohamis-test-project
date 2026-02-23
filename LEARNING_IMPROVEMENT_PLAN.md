# Learning-System Verbesserungsplan

Kombination aus Reflection (Option 1) + Failed Attempts (Option 2)

## Vision

VORHER: Ticket -> Agent -> DONE -> LearningEpisode (nur Endergebnis)
NACHHER: Ticket -> Agent -> TESTING -> Mensch prueft -> Daumen hoch/runter
                -> Failed Attempts gespeichert + Reflection generiert

## Phase 1: Datenbank-Schema

### Neue Tabelle: ticket_iterations
Speichert jede ORPA-Iteration separat.

Felder:
- id, ticket_id, iteration_number, orpa_state
- intended_action, tools_planned, tools_executed
- execution_success, error_occurred, error_message, error_type
- created_at

### Erweiterte Tabelle: learnings
- learning_type: "success", "correction", "lesson", "anti_pattern"
- problem, attempted_solution, final_solution
- reflection, key_takeaway
- iteration_ids (JSON-Array)
- human_feedback

### Neue Spalten in tickets
- human_approved (BOOLEAN)
- human_feedback (TEXT)
- approved_by, approved_at
- testing_notes

## Phase 2: Backend API

Neue Endpoints:
- POST /tickets/{id}/approve
- POST /tickets/{id}/request-changes
- GET /tickets/{id}/iterations
- GET /learnings

## Phase 3: Agent-Modifikationen

1. Iteration-Tracking in jeder ORPA-Phase
2. Fehler-Klassifizierung (file_not_found, permission_denied, etc.)
3. Reflection-Generierung via LLM
4. Enhanced Learning mit Failed Attempts

## Phase 4: Memory-System

Neue Methoden:
- record_enhanced_learning()
- store_anti_pattern()
- store_lesson()
- get_enhanced_relevant_learnings()

## Phase 5: Frontend

- Review-Screen mit Iterationen-Timeline
- Star-Rating fuer Feedback
- Textarea fuer Feedback
- Buttons: Erfolgreich / Aenderungen / Fehlgeschlagen

## Phase 6: Workflow

Neuer Status-Flow:
BACKLOG -> IN_PROGRESS -> TESTING -> APPROVED -> DONE
                              |
                              -> CHANGES_REQUESTED -> IN_PROGRESS

## Phase 7: Migration

- Feature-Flags fuer schrittweise Einfuehrung
- Migration der alten Learnings
- Legacy-Mode verfuegbar

## Phase 8: Tests

- Unit-Tests fuer Iteration-Tracking
- Integration-Tests fuer Approval-Flow
- Tests fuer Reflection-Generierung

## Zusammenfassung

Breaking Changes: NEIN (dank Feature-Flags)

Nach Implementation:
- Agent lernt aus jedem Fehler
- Selbst-Reflexion moeglich
- Menschliches Feedback wird einbezogen
- Anti-Patterns werden vermieden
