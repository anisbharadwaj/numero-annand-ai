stages:
  - name: warn
    threshold: 0.7
  - name: force_mfa
    threshold: 0.85
  - name: revoke_tokens
    threshold: 0.95
require_confirmation_for: ["revoke_tokens","isolate_endpoint"]
