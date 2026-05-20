package com.example.cicdpractice.content;

import com.example.cicdpractice.user.UserAccount;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "comments")
public class Comment {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    private Content content;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    private UserAccount author;

    @Column(nullable = false, length = 1000)
    private String message;

    @Column(nullable = false)
    private Instant createdAt;

    protected Comment() {
    }

    public static Comment create(Content content, UserAccount author, String message) {
        Comment comment = new Comment();
        comment.content = content;
        comment.author = author;
        comment.message = message;
        comment.createdAt = Instant.now();
        return comment;
    }

    public Long getId() {
        return id;
    }

    public Content getContent() {
        return content;
    }

    public UserAccount getAuthor() {
        return author;
    }

    public String getMessage() {
        return message;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
