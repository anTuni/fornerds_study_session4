package com.example.cicdpractice.auth;

import com.example.cicdpractice.user.UserAccount;
import com.example.cicdpractice.user.UserRepository;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Service;

@Service
public class AuthService {
    private final UserRepository users;
    private final SecureRandom secureRandom = new SecureRandom();
    private final Map<String, SessionToken> sessions = new ConcurrentHashMap<>();

    public AuthService(UserRepository users) {
        this.users = users;
    }

    public String issueToken(UserAccount user) {
        byte[] bytes = new byte[32];
        secureRandom.nextBytes(bytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        sessions.put(token, new SessionToken(user.getId(), Instant.now().plusSeconds(3600)));
        return token;
    }

    public Optional<UserAccount> findByToken(String token) {
        SessionToken session = sessions.get(token);
        if (session == null || session.expiresAt().isBefore(Instant.now())) {
            sessions.remove(token);
            return Optional.empty();
        }
        return users.findById(session.userId()).filter(UserAccount::isActive);
    }

    private record SessionToken(Long userId, Instant expiresAt) {
    }
}
