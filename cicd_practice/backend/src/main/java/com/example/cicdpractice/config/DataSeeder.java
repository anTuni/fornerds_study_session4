package com.example.cicdpractice.config;

import com.example.cicdpractice.content.Content;
import com.example.cicdpractice.content.ContentRepository;
import com.example.cicdpractice.content.ContentStatus;
import com.example.cicdpractice.user.Role;
import com.example.cicdpractice.user.UserAccount;
import com.example.cicdpractice.user.UserRepository;
import java.time.Instant;
import java.util.List;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class DataSeeder {
    @Bean
    CommandLineRunner seedData(UserRepository users, ContentRepository contents, PasswordEncoder passwordEncoder) {
        return args -> {
            if (users.count() > 0) {
                return;
            }

            UserAccount admin = users.save(UserAccount.create("admin@example.com", "관리자", passwordEncoder.encode("admin1234"), Role.ADMIN));
            UserAccount editor = users.save(UserAccount.create("editor@example.com", "콘텐츠 담당자", passwordEncoder.encode("editor1234"), Role.EDITOR));
            UserAccount user = users.save(UserAccount.create("user@example.com", "일반 사용자", passwordEncoder.encode("user1234"), Role.USER));

            contents.saveAll(List.of(
                    Content.create("보안 공지", "정기 보안 점검이 예정되어 있습니다.", ContentStatus.PUBLISHED, admin, Instant.now().minusSeconds(86400)),
                    Content.create("신규 기능 안내", "콘텐츠 승인 워크플로우가 추가되었습니다.", ContentStatus.PUBLISHED, editor, Instant.now().minusSeconds(43200)),
                    Content.create("비공개 초안", "관리자 검토 전 초안입니다.", ContentStatus.DRAFT, editor, Instant.now())
            ));

            users.save(user);
        };
    }
}
