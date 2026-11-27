-- =============================================================
--  增量迁移 005：站点公告（首页右侧资讯栏）
--  执行：mysql -u root -p novel_platform < db/migrations/005_site_notice.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `site_notice` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title`      VARCHAR(120)    NOT NULL,
  `content`    VARCHAR(500)    NOT NULL DEFAULT '',
  `category`   VARCHAR(20)     NOT NULL DEFAULT '公告',
  `is_top`     TINYINT         NOT NULL DEFAULT 0,
  `status`     TINYINT         NOT NULL DEFAULT 1,
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_list` (`status`, `is_top`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站点公告';