-- =============================================================
--  增量迁移 001：钱包（签到 + 充值）
--  用于已经建过库的环境；全新安装直接用 schema.sql 即可
--  执行：mysql -u root -p novel_platform < db/migrations/001_wallet.sql
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

ALTER TABLE `sys_user`
  ADD COLUMN `coin`       INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '软妹币余额（充值货币）' AFTER `bio`,
  ADD COLUMN `watermelon` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '西瓜（签到积分）'       AFTER `coin`;

CREATE TABLE IF NOT EXISTS `user_sign_in` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT UNSIGNED NOT NULL,
  `sign_date`  DATE            NOT NULL,
  `reward`     INT UNSIGNED    NOT NULL DEFAULT 1,
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_date` (`user_id`, `sign_date`),
  CONSTRAINT `fk_sign_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='签到记录表';

CREATE TABLE IF NOT EXISTS `recharge_order` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `order_no`     VARCHAR(32)     NOT NULL,
  `user_id`      BIGINT UNSIGNED NOT NULL,
  `amount_fen`   INT UNSIGNED    NOT NULL,
  `coin`         INT UNSIGNED    NOT NULL,
  `status`       TINYINT         NOT NULL DEFAULT 0,
  `remark`       VARCHAR(200)    NOT NULL DEFAULT '',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `paid_at`      DATETIME                 DEFAULT NULL,
  `confirmed_by` BIGINT UNSIGNED          DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_status` (`user_id`, `status`, `created_at`),
  KEY `idx_status` (`status`, `created_at`),
  CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='充值订单表';