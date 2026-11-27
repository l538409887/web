USE novel_platform;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `author_follow` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id`    BIGINT UNSIGNED NOT NULL                COMMENT '关注者',
  `author_id`  BIGINT UNSIGNED NOT NULL                COMMENT '被关注的作者',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_author` (`user_id`, `author_id`),
  KEY `idx_author` (`author_id`),
  CONSTRAINT `fk_af_user`   FOREIGN KEY (`user_id`)   REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_af_author` FOREIGN KEY (`author_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='作者关注';