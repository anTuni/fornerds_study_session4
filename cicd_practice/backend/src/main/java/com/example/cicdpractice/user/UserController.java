package com.example.cicdpractice.user;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/users")
public class UserController {
    private final UserRepository users;

    public UserController(UserRepository users) {
        this.users = users;
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public List<UserSummary> list() {
        return users.findAll().stream().map(UserSummary::from).toList();
    }

    @PatchMapping("/{id}/role")
    @PreAuthorize("hasRole('ADMIN')")
    public UserSummary changeRole(@PathVariable Long id, @Valid @RequestBody RoleChangeRequest request) {
        UserAccount user = users.findById(id).orElseThrow();
        user.changeRole(request.role());
        return UserSummary.from(users.save(user));
    }

    @PatchMapping("/{id}/profile")
    public UserSummary updateProfile(@AuthenticationPrincipal UserPrincipal principal,
                                     @PathVariable Long id,
                                     @Valid @RequestBody ProfileUpdateRequest request) {
        UserAccount user = users.findById(id).orElseThrow();
        if (request.displayName() != null) {
            user.setDisplayName(request.displayName());
        }
        if (request.role() != null) {
            user.changeRole(request.role());
        }
        return UserSummary.from(users.save(user));
    }

    public record RoleChangeRequest(@NotNull Role role) {
    }

    public record ProfileUpdateRequest(@Size(max = 100) String displayName, Role role) {
    }

    public record UserSummary(Long id, String email, String displayName, Role role, boolean active) {
        public static UserSummary from(UserAccount user) {
            return new UserSummary(user.getId(), user.getEmail(), user.getDisplayName(), user.getRole(), user.isActive());
        }
    }
}
