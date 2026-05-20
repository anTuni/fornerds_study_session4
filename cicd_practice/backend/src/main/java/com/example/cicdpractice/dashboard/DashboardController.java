package com.example.cicdpractice.dashboard;

import com.example.cicdpractice.content.ContentRepository;
import com.example.cicdpractice.content.ContentStatus;
import com.example.cicdpractice.user.UserRepository;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/dashboard")
public class DashboardController {
    private final UserRepository users;
    private final ContentRepository contents;

    public DashboardController(UserRepository users, ContentRepository contents) {
        this.users = users;
        this.contents = contents;
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public DashboardSummary summary() {
        return new DashboardSummary(
                users.count(),
                contents.count(),
                contents.findByStatusOrderByUpdatedAtDesc(ContentStatus.PUBLISHED).size()
        );
    }

    public record DashboardSummary(long users, long contents, long publishedContents) {
    }
}
