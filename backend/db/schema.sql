CREATE TABLE audits (
  id TEXT PRIMARY KEY,
  job_id TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  summary JSONB
);

CREATE TABLE flagged_examples (
  id SERIAL PRIMARY KEY,
  audit_id TEXT REFERENCES audits(id),
  unique_id TEXT,
  explanation TEXT,
  redacted_payload JSONB
);

CREATE TABLE outbound_queue (
  id SERIAL PRIMARY KEY,
  action_type TEXT,
  payload JSONB,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE enforcement_log (
  id SERIAL PRIMARY KEY,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actor TEXT,
  action TEXT,
  justification TEXT,
  rollback_instructions TEXT
);
