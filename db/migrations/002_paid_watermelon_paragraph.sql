-- =============================================================
--  增量迁移 002：付费 / 投喂西瓜 / 间贴
--  执行：mysql -u root -p novel_platform < db/migrations/002_paid_watermelon_paragraph.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

-- 书籍：付费、收入、西瓜数、间贴数
ALTER TABLE `book`
  ADD COLUMN `is_paid`                 TINYINT      NOT NULL DEFAULT 0 COMMENT '0免费 1付费' AFTER `score`,
  ADD COLUMN `price_coin`              INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '整本价格（软妹币）' AFTER `is_paid`,
  ADD COLUMN `revenue_coin`            INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计订阅收入（软妹币）' AFTER `price_coin`,
  ADD COLUMN `watermelon_count`        INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '被投喂西瓜总数' AFTER `revenue_coin`,
  ADD COLUMN `paragraph_comment_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '间贴总数' AFTER `watermelon_count`;

-- 购买记录
CREATE TABLE IF NOT EXISTS `book_purchase` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `book_id`    BIGINT UNSIGNED NOT NULL,
  `coin`       INT UNSIGNED    NOT NULL COMMENT '实际支付软妹币',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_book` (`user_id`, `book_id`),
  KEY `idx_book` (`book_id`),
  CONSTRAINT `fk_purchase_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_purchase_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`)     ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍购买记录';

-- 投喂西瓜流水
CREATE TABLE IF NOT EXISTS `book_watermelon_log` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `book_id`    BIGINT UNSIGNED NOT NULL,
  `count`      INT UNSIGNED    NOT NULL DEFAULT 1,
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_book` (`book_id`),
  KEY `idx_user` (`user_id`, `created_at`),
  CONSTRAINT `fk_wm_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_wm_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`)     ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='投喂西瓜流水';

-- 间贴（段落评论）
CREATE TABLE IF NOT EXISTS `paragraph_comment` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `book_id`         BIGINT UNSIGNED NOT NULL,
  `chapter_id`      BIGINT UNSIGNED NOT NULL,
  `paragraph_index` INT UNSIGNED    NOT NULL COMMENT '段落序号，从 0 开始',
  `user_id`         BIGINT UNSIGNED NOT NULL,
  `content`         VARCHAR(300)    NOT NULL,
  `like_count`      INT UNSIGNED    NOT NULL DEFAULT 0,
  `dislike_count`   INT UNSIGNED    NOT NULL DEFAULT 0,
  `report_count`    INT UNSIGNED    NOT NULL DEFAULT 0,
  `status`          TINYINT         NOT NULL DEFAULT 1 COMMENT '1正常 0已隐藏',
  `created_at`      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_para` (`chapter_id`, `paragraph_index`, `status`, `created_at`),
  KEY `idx_book` (`book_id`),
  KEY `idx_user` (`user_id`),
  CONSTRAINT `fk_pc_book`    FOREIGN KEY (`book_id`)    REFERENCES `book` (`id`)         ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pc_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pc_user`    FOREIGN KEY (`user_id`)    REFERENCES `sys_user` (`id`)     ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='间贴（段落评论）';

-- 间贴反应（赞 / 踩 / 举报）
CREATE TABLE IF NOT EXISTS `paragraph_reaction` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `comment_id` BIGINT UNSIGNED NOT NULL,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `reaction`   TINYINT         NOT NULL COMMENT '1赞 2踩 3举报',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_comment_user` (`comment_id`, `user_id`),
  CONSTRAINT `fk_pr_comment` FOREIGN KEY (`comment_id`) REFERENCES `paragraph_comment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pr_user`    FOREIGN KEY (`user_id`)    REFERENCES `sys_user` (`id`)         ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='间贴反应';