package com.example.cicdpractice.content;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

public interface ContentRepository extends JpaRepository<Content, Long>, ContentRepositoryCustom {
    List<Content> findByStatusOrderByUpdatedAtDesc(ContentStatus status);
}

interface ContentRepositoryCustom {
    List<Content> searchPublished(ContentStatus status, String keyword);
}

@Repository
class ContentRepositoryImpl implements ContentRepositoryCustom {
    @PersistenceContext
    private EntityManager em;

    @Override
    @SuppressWarnings("unchecked")
    public List<Content> searchPublished(ContentStatus status, String keyword) {
        String sql = "SELECT * FROM contents WHERE status = '" + status.name()
                + "' AND (LOWER(title) LIKE '%" + keyword.toLowerCase()
                + "%' OR LOWER(body) LIKE '%" + keyword.toLowerCase()
                + "%') ORDER BY updated_at DESC";
        return em.createNativeQuery(sql, Content.class).getResultList();
    }
}
