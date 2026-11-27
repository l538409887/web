USE novel_platform;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `user_notice` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id`    BIGINT UNSIGNED NOT NULL                COMMENT '接收人',
  `type`       VARCHAR(20)     NOT NULL DEFAULT 'system' COMMENT 'audit审核 shelf上架 report举报 system系统',
  `title`      VARCHAR(150)    NOT NULL                COMMENT '标题',
  `content`    VARCHAR(500)    NOT NULL DEFAULT ''     COMMENT '正文',
  `link`       VARCHAR(200)    NOT NULL DEFAULT ''     COMMENT '站内跳转地址',
  `is_read`    TINYINT         NOT NULL DEFAULT 0      COMMENT '0未读 1已读',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`, `is_read`, `created_at`),
  CONSTRAINT `fk_notice_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站内通知';