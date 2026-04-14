# Daily Log - 2026-02-20

## #sales
- 14:00 Josh: Call with Acme Corp went well. They're very interested in upgrading to Enterprise tier.
- 14:05 Josh: One thing - their IT team specifically asked about SAML SSO. I told them we'd have that after the auth migration. They're expecting it by end of Q1.
- 14:10 Josh: @Alan FYI - Acme is our biggest prospect, $80K ARR potential

## #engineering
- 15:00 Alan: Auth migration is scoped - replacing the session-based system with JWT tokens. OAuth2 flows for Google and GitHub login. No SAML in this phase - it's a completely different protocol and would add 3 weeks.

# Daily Log - 2026-03-07

## #engineering
- 10:00 Alan: Auth migration is done! JWT tokens working, OAuth2 flows for Google and GitHub are live. Closing the ticket.
- 10:05 Alan: Moving on to billing reconciliation full time now.
