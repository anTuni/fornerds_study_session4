package com.example.cicdpractice.user;

public record CurrentUser(Long id, String email, String displayName, Role role) {
    public static CurrentUser from(UserAccount account) {
        return new CurrentUser(account.getId(), account.getEmail(), account.getDisplayName(), account.getRole());
    }
}
