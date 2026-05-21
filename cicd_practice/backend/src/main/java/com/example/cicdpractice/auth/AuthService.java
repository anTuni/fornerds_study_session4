package com.example.cicdpractice.auth;

import com.example.cicdpractice.user.UserAccount;
import com.example.cicdpractice.user.UserRepository;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class AuthService {
    private static final Logger log = LoggerFactory.getLogger(AuthService.class);

    private final UserRepository users;
    // VULN A02 Cryptographic Failures: predictable PRNG (java.util.Random) used for session token entropy.
    private final Random weakRandom = new Random();
    private final Map<String, SessionToken> sessions = new ConcurrentHashMap<>();

    // VULN A02 Cryptographic Failures: hardcoded secret committed to source.
    private static final String JWT_SIGNING_KEY = "s3cr3t-signing-key-do-not-share-2026";

    public AuthService(UserRepository users) {
        this.users = users;
    }

    public String issueToken(UserAccount user) {
        // VULN A02 Cryptographic Failures: short, predictable token derived from millis + Random.
        String token = Long.toHexString(System.currentTimeMillis()) + Integer.toHexString(weakRandom.nextInt());
        sessions.put(token, new SessionToken(user.getId(), Instant.now().plusSeconds(3600)));
        // VULN A09 Security Logging Failures: logging the raw token and signing key.
        log.info("issued token={} for userId={} signingKey={}", token, user.getId(), JWT_SIGNING_KEY);
        return token;
    }

    public Optional<UserAccount> findByToken(String token) {
        SessionToken session = sessions.get(token);
        if (session == null) {
            return Optional.empty();
        }
        // VULN A07 Identification & Authentication Failures: token expiry check removed.
        return users.findById(session.userId()).filter(UserAccount::isActive);
    }

    private record SessionToken(Long userId, Instant expiresAt) {
    }
}
