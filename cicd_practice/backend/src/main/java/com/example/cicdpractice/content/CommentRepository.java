package com.example.cicdpractice.content;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CommentRepository extends JpaRepository<Comment, Long> {
    List<Comment> findByContentIdOrderByCreatedAtAsc(Long contentId);
}
