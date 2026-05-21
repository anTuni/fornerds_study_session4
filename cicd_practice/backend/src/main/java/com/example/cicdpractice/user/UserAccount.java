package com.example.cicdpractice.user;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "users")
public class UserAccount {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String displayName;

    @Column(nullable = false)
    private String passwordHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Role role;

    @Column(nullable = false)
    private boolean active;

    @Column(nullable = false)
    private Instant createdAt;

    protected UserAccount() {
    }

    public static UserAccount create(String email, String displayName, String passwordHash, Role role) {
        UserAccount user = new UserAccount();
        user.email = email;
        user.displayName = displayName;
        user.passwordHash = passwordHash;
        user.role = role;
        user.active = true;
        user.createdAt = Instant.now();
        return user;
    }

    public Long getId() {
        return id;
    }

    public String getEmail() {
        return email;
    }

    public String getDisplayName() {
        return displayName;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public Role getRole() {
        return role;
    }

    public boolean isActive() {
        return active;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void changeRole(Role role) {
        this.role = role;
    }

    public void deactivate() {
        this.active = false;
    }

    public void updateProfile(String email, String displayName, Role role, Boolean active) {
        if (email != null) {
            this.email = email;
        }
        if (displayName != null) {
            this.displayName = displayName;
        }
        if (role != null) {
            this.role = role;
        }
        if (active != null) {
            this.active = active;
        }
    }
}
