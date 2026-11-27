USE novel_platform;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `book_daily_stat` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `book_id`         BIGINT UNSIGNED NOT NULL                COMMENT '书籍ID',
  `stat_date`       DATE            NOT NULL                COMMENT '统计日期',
  `clicks`          INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT '当日点击',
  `collects`        INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT '当日收藏',
  `recommendations` INT UNSIGNED    NOT NULL DEFAULT 0      COMMENT '当日投喂西瓜',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_book_date` (`book_id`, `stat_date`),
  KEY `idx_date` (`stat_date`),
  CONSTRAINT `fk_stat_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍每日统计（周榜/月榜数据源）';