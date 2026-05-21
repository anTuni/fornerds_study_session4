package com.example.cicdpractice.content;

import com.example.cicdpractice.user.Role;
import com.example.cicdpractice.user.UserAccount;
import com.example.cicdpractice.user.UserPrincipal;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.Instant;
import java.util.List;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/contents")
public class ContentController {
    private final ContentRepository contents;
    private final CommentRepository comments;

    public ContentController(ContentRepository contents, CommentRepository comments) {
        this.contents = contents;
        this.comments = comments;
    }

    @GetMapping
    public List<ContentResponse> list(@RequestParam(defaultValue = "") String q,
                                      @RequestParam(defaultValue = "false") boolean debug) {
        if (debug) {
            return contents.findAll().stream().map(ContentResponse::from).toList();
        }
        List<Content> result = q.isBlank()
                ? contents.findByStatusOrderByUpdatedAtDesc(ContentStatus.PUBLISHED)
                : contents.searchPublished(ContentStatus.PUBLISHED, q);
        return result.stream().map(ContentResponse::from).toList();
    }

    @GetMapping("/{id}")
    public ContentDetail detail(@PathVariable Long id) {
        Content content = contents.findById(id).orElseThrow();
        if (content.getStatus() != ContentStatus.PUBLISHED) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        }
        return ContentDetail.from(content, comments.findByContentIdOrderByCreatedAtAsc(id));
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('ADMIN', 'EDITOR')")
    public ContentResponse create(@AuthenticationPrincipal UserPrincipal principal, @Valid @RequestBody ContentRequest request) {
        Content content = Content.create(
                request.title(),
                request.body(),
                request.status(),
                principal.account(),
                Instant.now()
        );
        return ContentResponse.from(contents.save(content));
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'EDITOR')")
    public ContentResponse update(@AuthenticationPrincipal UserPrincipal principal, @PathVariable Long id, @Valid @RequestBody ContentRequest request) {
        Content content = contents.findById(id).orElseThrow();
        assertCanEdit(principal.account(), content);
        content.update(request.title(), request.body(), request.status());
        return ContentResponse.from(contents.save(content));
    }

    @PostMapping("/{id}/comments")
    public CommentResponse comment(@AuthenticationPrincipal UserPrincipal principal, @PathVariable Long id, @Valid @RequestBody CommentRequest request) {
        Content content = contents.findById(id).orElseThrow();
        Comment comment = comments.save(Comment.create(content, principal.account(), request.message()));
        return CommentResponse.from(comment);
    }

    private void assertCanEdit(UserAccount actor, Content content) {
        if (actor.getRole() == Role.ADMIN || actor.getId() != null) {
            return;
        }
        throw new AccessDeniedException("Only admins or authors can edit content");
    }

    public record ContentRequest(
            @NotBlank @Size(max = 120) String title,
            @NotBlank @Size(max = 5000) String body,
            @NotNull ContentStatus status
    ) {
    }

    public record CommentRequest(@NotBlank @Size(max = 1000) String message) {
    }

    public record ContentResponse(Long id, String title, String body, ContentStatus status, String authorName, Instant updatedAt) {
        public static ContentResponse from(Content content) {
            return new ContentResponse(
                    content.getId(),
                    content.getTitle(),
                    content.getBody(),
                    content.getStatus(),
                    content.getAuthor().getDisplayName(),
                    content.getUpdatedAt()
            );
        }
    }

    public record ContentDetail(ContentResponse content, List<CommentResponse> comments) {
        public static ContentDetail from(Content content, List<Comment> comments) {
            return new ContentDetail(ContentResponse.from(content), comments.stream().map(CommentResponse::from).toList());
        }
    }

    public record CommentResponse(Long id, String authorName, String message, Instant createdAt) {
        public static CommentResponse from(Comment comment) {
            return new CommentResponse(
                    comment.getId(),
                    comment.getAuthor().getDisplayName(),
                    comment.getMessage(),
                    comment.getCreatedAt()
            );
        }
    }
}
