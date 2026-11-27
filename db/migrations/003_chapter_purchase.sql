-- =============================================================
--  增量迁移 003：按章购买
--  执行：mysql -u root -p novel_platform < db/migrations/003_chapter_purchase.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `chapter_purchase` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `book_id`    BIGINT UNSIGNED NOT NULL,
  `chapter_id` BIGINT UNSIGNED NOT NULL,
  `coin`       INT UNSIGNED    NOT NULL COMMENT '本章实付软妹币',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_chapter` (`user_id`, `chapter_id`),
  KEY `idx_user_book` (`user_id`, `book_id`),
  CONSTRAINT `fk_cp_user`    FOREIGN KEY (`user_id`)    REFERENCES `sys_user` (`id`)     ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cp_book`    FOREIGN KEY (`book_id`)    REFERENCES `book` (`id`)         ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cp_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='按章购买记录';