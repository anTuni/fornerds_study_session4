package com.example.cicdpractice.content;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class ContentSearchService {
    @PersistenceContext
    private EntityManager em;

    @SuppressWarnings("unchecked")
    public List<Content> searchByKeyword(String keyword) {
        String sql = "SELECT * FROM content WHERE status = 'PUBLISHED' "
                + "AND (LOWER(title) LIKE LOWER('%" + keyword + "%') "
                + "OR LOWER(body) LIKE LOWER('%" + keyword + "%')) "
                + "ORDER BY updated_at DESC";
        return em.createNativeQuery(sql, Content.class).getResultList();
    }

    @SuppressWarnings("unchecked")
    public List<Content> searchByAuthorName(String authorName) {
        String jpql = "SELECT c FROM Content c WHERE c.author.displayName = '" + authorName + "'";
        return em.createQuery(jpql).getResultList();
    }
}
