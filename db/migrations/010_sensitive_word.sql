USE novel_platform;
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `sensitive_word` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `word`       VARCHAR(50)     NOT NULL                COMMENT '敏感词',
  `level`      VARCHAR(10)     NOT NULL DEFAULT 'review' COMMENT 'block直接拦截 review转人工',
  `category`   VARCHAR(20)     NOT NULL DEFAULT '其他'  COMMENT '广告/辱骂/违禁/其他',
  `is_active`  TINYINT         NOT NULL DEFAULT 1      COMMENT '1启用 0停用',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_word` (`word`),
  KEY `idx_level` (`level`, `is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='敏感词库';

-- 演示词库：真实部署时应导入完整词表。这里只放广告/辱骂类的通用示例。
INSERT IGNORE INTO `sensitive_word` (`word`, `level`, `category`) VALUES
('加微信', 'block', '广告'),
('加QQ', 'block', '广告'),
('扫码领', 'block', '广告'),
('代写论文', 'block', '广告'),
('刷单', 'block', '广告'),
('返利', 'review', '广告'),
('私聊下单', 'block', '广告'),
('免费领取', 'review', '广告'),
('兼职日结', 'block', '广告'),
('推广链接', 'review', '广告'),
('垃圾', 'review', '辱骂'),
('骗子', 'review', '辱骂'),
('滚蛋', 'review', '辱骂'),
('一群废物', 'block', '辱骂'),
('违禁示例词', 'block', '违禁');