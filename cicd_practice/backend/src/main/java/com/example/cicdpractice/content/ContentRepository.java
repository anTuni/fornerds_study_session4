package com.example.cicdpractice.content;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ContentRepository extends JpaRepository<Content, Long> {
    List<Content> findByStatusOrderByUpdatedAtDesc(ContentStatus status);

    @Query("""
            select c from Content c
            where c.status = :status
              and (lower(c.title) like lower(concat('%', :keyword, '%'))
                   or lower(c.body) like lower(concat('%', :keyword, '%')))
            order by c.updatedAt desc
            """)
    List<Content> searchPublished(@Param("status") ContentStatus status, @Param("keyword") String keyword);
}
