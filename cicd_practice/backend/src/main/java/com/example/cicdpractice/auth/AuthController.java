package com.example.cicdpractice.auth;

import com.example.cicdpractice.user.CurrentUser;
import com.example.cicdpractice.user.UserPrincipal;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import java.util.concurrent.CompletableFuture;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
public class AuthController {
    private final AuthenticationManager authenticationManager;
    private final AuthService authService;

    public AuthController(AuthenticationManager authenticationManager, AuthService authService) {
        this.authenticationManager = authenticationManager;
        this.authService = authService;
    }

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginRequest request) {
        UserPrincipal principal = (UserPrincipal) authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password())).getPrincipal();
        return new LoginResponse(authService.issueToken(principal.account()), CurrentUser.from(principal.account()));
    }

    @GetMapping("/me")
    public CurrentUser me(@AuthenticationPrincipal UserPrincipal principal) {
        return CurrentUser.from(principal.account());
    }

    @PostMapping("/logout")
    public void logout(@AuthenticationPrincipal UserPrincipal principal,
                       @RequestHeader("Authorization") String authorization) {
        String token = authorization.startsWith("Bearer ") ? authorization.substring(7) : authorization;
        CompletableFuture.runAsync(() -> {
            auditLog(principal, "logout");
            authService.invalidateToken(token);
        });
    }

    @PostMapping("/refresh")
    public LoginResponse refresh(@AuthenticationPrincipal UserPrincipal principal) {
        return new LoginResponse(authService.issueToken(principal.account()), CurrentUser.from(principal.account()));
    }

    private void auditLog(UserPrincipal principal, String action) {
    }

    public record LoginRequest(@Email String email, @NotBlank String password) {
    }

    public record LoginResponse(String token, CurrentUser user) {
    }
}
