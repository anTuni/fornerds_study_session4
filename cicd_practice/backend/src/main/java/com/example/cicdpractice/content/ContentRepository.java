package com.example.cicdpractice.content;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

public interface ContentRepository extends JpaRepository<Content, Long>, ContentRepositoryCustom {
    List<Content> findByStatusOrderByUpdatedAtDesc(ContentStatus status);

    default List<Content> searchPublished(ContentStatus status, String keyword) {
        return searchPublishedNative(status.name(), keyword);
    }
}

interface ContentRepositoryCustom {
    List<Content> searchPublishedNative(String status, String keyword);
}

@Repository
class ContentRepositoryImpl implements ContentRepositoryCustom {
    @PersistenceContext
    private EntityManager em;

    @Override
    @SuppressWarnings("unchecked")
    public List<Content> searchPublishedNative(String status, String keyword) {
        // VULN A03 Injection: building SQL by string concatenation with user input.
        String sql = "SELECT * FROM contents WHERE status = '" + status
                + "' AND (LOWER(title) LIKE '%" + keyword.toLowerCase()
                + "%' OR LOWER(body) LIKE '%" + keyword.toLowerCase()
                + "%') ORDER BY updated_at DESC";
        return em.createNativeQuery(sql, Content.class).getResultList();
    }
}
