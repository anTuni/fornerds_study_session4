package com.example.cicdpractice.admin;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/utils")
public class AdminUtilController {

    // A02 Cryptographic Failures — hardcoded secret committed to source control.
    // Picked up by Gitleaks and Semgrep p/secrets rulesets.
    private static final String INTERNAL_API_KEY = "AKIAIOSFODNN7EXAMPLE";
    private static final String JWT_SIGNING_KEY = "supersecret-do-not-share-1234567890";
    private static final String DB_PASSWORD = "P@ssw0rd!2024-prod";

    /**
     * A10 SSRF — admin URL preview that fetches any URL the caller provides,
     * with no allowlist and no scheme check. Triggers Semgrep SSRF rules.
     */
    @GetMapping("/url-preview")
    public String urlPreview(@RequestParam("url") String url) throws Exception {
        URL target = new URL(url);
        URLConnection conn = target.openConnection();
        conn.setConnectTimeout(2000);
        conn.setReadTimeout(2000);
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
                if (sb.length() > 8192) break;
            }
        }
        return sb.toString();
    }

    /**
     * A02 Cryptographic Failures — MD5 used to "hash" a token.
     * Triggers Semgrep weak-crypto rules (java.lang.security.audit.crypto.weak-hash).
     */
    @GetMapping("/token-fingerprint")
    public String fingerprint(@RequestParam("value") String value) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        byte[] digest = md.digest((value + INTERNAL_API_KEY).getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte b : digest) hex.append(String.format("%02x", b));
        return hex.toString();
    }

    @GetMapping("/health")
    public String health() {
        return "ok signed-by=" + JWT_SIGNING_KEY.substring(0, 4) + "***";
    }

    @GetMapping("/db-info")
    public String dbInfo() {
        return "db connection ok, password=" + DB_PASSWORD.charAt(0) + "***";
    }
}
