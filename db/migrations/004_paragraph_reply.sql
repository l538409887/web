-- =============================================================
--  增量迁移 004：间贴回复
--  执行：mysql -u root -p novel_platform < db/migrations/004_paragraph_reply.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

ALTER TABLE `paragraph_comment`
  ADD COLUMN `parent_id`   BIGINT UNSIGNED DEFAULT NULL COMMENT '父间贴ID，NULL 为顶层' AFTER `book_id`,
  ADD COLUMN `reply_count` INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '回复数' AFTER `report_count`,
  ADD KEY `idx_parent` (`parent_id`),
  ADD CONSTRAINT `fk_pc_parent` FOREIGN KEY (`parent_id`) REFERENCES `paragraph_comment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE;