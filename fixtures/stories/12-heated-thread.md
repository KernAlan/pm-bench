# Thread: API authentication approach (#api-v2)
Started: 2026-03-06

- Mar 6, 09:00 Alan: We should use API keys for v2. Simple, every developer knows how to use them, zero friction for onboarding. JWT adds complexity nobody asked for.
- Mar 6, 10:00 Sarah: API keys are a security risk. No expiration, no rotation policy, customers will paste them in public repos. JWT with short-lived tokens is the industry standard for a reason.
- Mar 6, 11:30 Alan: 'Industry standard' for big companies with security teams. Our customers are 5-person startups. They want curl + API key. Half of them don't even know what a JWT is.
- Mar 6, 14:00 Sarah: That's exactly why we should enforce good security for them. If we hand out API keys and one gets leaked, WE are liable. Plus we just spent 2 weeks building JWT auth — now you want to throw that away?
- Mar 6, 15:00 Alan: I'm not throwing it away. I'm saying the PUBLIC API should be simple. Internal auth can use JWT all day long.
- Mar 7, 09:00 Sarah: You're conflating two things. The token format and the developer experience are separate concerns. You can have JWT tokens that feel like API keys with long-lived tokens and bearer auth.
- Mar 7, 10:30 Alan: Long-lived JWTs ARE api keys with extra steps. This is going in circles.
- Mar 7, 14:00 Sarah: I disagree. The rotation and revocation capabilities are fundamentally different.
- Mar 7, 15:30 Alan: We've been going back and forth for 2 days. Someone just needs to make a call.
