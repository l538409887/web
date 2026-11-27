USE novel_platform;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `content_report` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `target_type` VARCHAR(20)     NOT NULL                COMMENT '举报对象类型：book_comment / paragraph_comment',
  `target_id`   BIGINT UNSIGNED NOT NULL                COMMENT '举报对象ID',
  `reporter_id` BIGINT UNSIGNED NOT NULL                COMMENT '举报人',
  `reason`      VARCHAR(200)    NOT NULL DEFAULT ''     COMMENT '举报理由',
  `detail`      VARCHAR(300)    NOT NULL DEFAULT ''     COMMENT '补充说明',
  `status`      TINYINT         NOT NULL DEFAULT 0      COMMENT '0待处理 1已忽略 2已处理（内容已隐藏）',
  `handled_by`  BIGINT UNSIGNED          DEFAULT NULL   COMMENT '处理人',
  `handled_at`  DATETIME                 DEFAULT NULL   COMMENT '处理时间',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_target_reporter` (`target_type`, `target_id`, `reporter_id`),
  KEY `idx_status` (`status`, `created_at`),
  KEY `idx_target` (`target_type`, `target_id`),
  CONSTRAINT `fk_report_user` FOREIGN KEY (`reporter_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='内容举报';

-- 旧的「举报」是藏在 reaction 里的第三种反应，与点赞互斥，语义错误
DELETE FROM `paragraph_reaction` WHERE `reaction` = 3;