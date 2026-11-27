-- =============================================================
--  增量迁移 012：公告封面图
--  执行：mysql -u root -p novel_platform < db/migrations/012_notice_cover.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

ALTER TABLE `site_notice`
  ADD COLUMN `cover` VARCHAR(200) NOT NULL DEFAULT '' COMMENT '封面图URL' AFTER `content`;