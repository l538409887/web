-- =============================================================
--  基于 Python 的轻量化 Web 小说平台
--  数据库建表脚本  schema.sql
--  MySQL 8.0+  字符集 utf8mb4 / 排序规则 utf8mb4_0900_ai_ci
--  执行方式：mysql -u root -p < db/schema.sql
--  幂等性：会先 DROP 同名表，请勿在已有生产数据上执行！
--
--  【本文件由生产库结构导出生成】
--    生成命令：mysqldump --no-data --compact --skip-add-drop-table novel_platform
--    共 23 张表，包含全部 12 次增量迁移后的最终结构。
--    修改表结构后请重新导出，不要手工编辑——手工维护曾导致
--    「books 表缺少 shelf_status 等迁移列」这种 clone 即报错的问题。
--
--  【安全说明】本机同时存在多个项目的数据库，本脚本：
--    1. 只 CREATE / USE `novel_platform`，全程不执行 DROP DATABASE；
--    2. 所有 DROP TABLE 均写成 `novel_platform`.`表名`，
--       即使默认库选错，也只会在 novel_platform 内生效；
--    3. 不动 information_schema / mysql / 其它任何库。
-- =============================================================

CREATE DATABASE IF NOT EXISTS `novel_platform`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE `novel_platform`;

SET NAMES utf8mb4;

-- 整个建表过程保持外键检查关闭：表按字母序创建，
-- 子表可能先于父表出现（如 author_follow 先于 sys_user），
-- 此时若打开检查会报 1824 Failed to open the referenced table。
SET FOREIGN_KEY_CHECKS = 0;

-- 全部 23 张表；外键检查已关闭，DROP 顺序不影响结果。
DROP TABLE IF EXISTS `novel_platform`.`book_daily_stat`;
DROP TABLE IF EXISTS `novel_platform`.`author_follow`;
DROP TABLE IF EXISTS `novel_platform`.`user_notice`;
DROP TABLE IF EXISTS `novel_platform`.`site_notice`;
DROP TABLE IF EXISTS `novel_platform`.`sensitive_word`;
DROP TABLE IF EXISTS `novel_platform`.`content_report`;
DROP TABLE IF EXISTS `novel_platform`.`paragraph_reaction`;
DROP TABLE IF EXISTS `novel_platform`.`paragraph_comment`;
DROP TABLE IF EXISTS `novel_platform`.`book_watermelon_log`;
DROP TABLE IF EXISTS `novel_platform`.`chapter_purchase`;
DROP TABLE IF EXISTS `novel_platform`.`book_purchase`;
DROP TABLE IF EXISTS `novel_platform`.`recharge_order`;
DROP TABLE IF EXISTS `novel_platform`.`user_sign_in`;
DROP TABLE IF EXISTS `novel_platform`.`book_vote`;
DROP TABLE IF EXISTS `novel_platform`.`book_comment`;
DROP TABLE IF EXISTS `novel_platform`.`reading_history`;
DROP TABLE IF EXISTS `novel_platform`.`user_bookshelf`;
DROP TABLE IF EXISTS `novel_platform`.`book_chapter`;
DROP TABLE IF EXISTS `novel_platform`.`book_tag_rel`;
DROP TABLE IF EXISTS `novel_platform`.`book_tag`;
DROP TABLE IF EXISTS `novel_platform`.`book`;
DROP TABLE IF EXISTS `novel_platform`.`book_category`;
DROP TABLE IF EXISTS `novel_platform`.`sys_user`;

CREATE TABLE `author_follow` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint unsigned NOT NULL COMMENT '关注者',
  `author_id` bigint unsigned NOT NULL COMMENT '被关注的作者',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_author` (`user_id`,`author_id`),
  KEY `idx_author` (`author_id`),
  CONSTRAINT `fk_af_author` FOREIGN KEY (`author_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_af_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='作者关注';
CREATE TABLE `book` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '书籍ID',
  `title` varchar(100) NOT NULL COMMENT '书名',
  `author_id` bigint unsigned NOT NULL COMMENT '作者ID -> sys_user.id',
  `category_id` int unsigned NOT NULL COMMENT '分类ID -> book_category.id',
  `cover` varchar(255) NOT NULL DEFAULT '' COMMENT '封面图地址',
  `intro` text NOT NULL COMMENT '简介',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0连载中 1已完结',
  `audit_status` tinyint NOT NULL DEFAULT '1' COMMENT '0待审核 1已通过 2已下架',
  `shelf_status` tinyint NOT NULL DEFAULT '0' COMMENT '0未上架 1上架申请中 2已上架 3上架被拒',
  `word_count` int unsigned NOT NULL DEFAULT '0' COMMENT '总字数（冗余）',
  `chapter_count` int unsigned NOT NULL DEFAULT '0' COMMENT '总章节数（冗余）',
  `click_count` bigint unsigned NOT NULL DEFAULT '0' COMMENT '点击数（冗余，供榜单）',
  `collect_count` int unsigned NOT NULL DEFAULT '0' COMMENT '收藏数（冗余）',
  `recommend_count` int unsigned NOT NULL DEFAULT '0' COMMENT '推荐票数（冗余）',
  `score` decimal(3,1) NOT NULL DEFAULT '0.0' COMMENT '评分 0.0~10.0',
  `is_paid` tinyint NOT NULL DEFAULT '0' COMMENT '0免费 1付费',
  `price_coin` int unsigned NOT NULL DEFAULT '0' COMMENT '整本价格（软妹币）',
  `revenue_coin` int unsigned NOT NULL DEFAULT '0' COMMENT '累计订阅收入（软妹币）',
  `watermelon_count` int unsigned NOT NULL DEFAULT '0' COMMENT '被投喂西瓜总数',
  `paragraph_comment_count` int unsigned NOT NULL DEFAULT '0' COMMENT '间贴总数',
  `last_chapter_id` bigint unsigned DEFAULT NULL COMMENT '最新章节ID（冗余）',
  `last_chapter_title` varchar(200) NOT NULL DEFAULT '' COMMENT '最新章节标题（冗余）',
  `last_update_at` datetime DEFAULT NULL COMMENT '最近更新时间（冗余）',
  `is_recommend` tinyint NOT NULL DEFAULT '0' COMMENT '1=首页推荐位',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_category` (`category_id`,`audit_status`),
  KEY `idx_author` (`author_id`),
  KEY `idx_update` (`last_update_at`),
  KEY `idx_click` (`click_count`),
  KEY `idx_recommend` (`is_recommend`,`click_count`),
  CONSTRAINT `fk_book_author` FOREIGN KEY (`author_id`) REFERENCES `sys_user` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_book_category` FOREIGN KEY (`category_id`) REFERENCES `book_category` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍表';
CREATE TABLE `book_category` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT '分类ID',
  `name` varchar(32) NOT NULL COMMENT '分类名称',
  `sort` int NOT NULL DEFAULT '0' COMMENT '排序值，越小越靠前',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍分类表';
CREATE TABLE `book_chapter` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '章节ID',
  `book_id` bigint unsigned NOT NULL COMMENT '所属书籍ID',
  `chapter_no` int unsigned NOT NULL COMMENT '章节序号，书内从1递增',
  `title` varchar(200) NOT NULL COMMENT '章节标题',
  `content` longtext NOT NULL COMMENT '正文，纯文本，\n 分段',
  `word_count` int unsigned NOT NULL DEFAULT '0' COMMENT '本章字数',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1正常 0已屏蔽',
  `audit_status` tinyint NOT NULL DEFAULT '1' COMMENT '0草稿 1待审核 2已通过 3未通过',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_book_no` (`book_id`,`chapter_no`),
  KEY `idx_book_status` (`book_id`,`status`),
  CONSTRAINT `fk_chapter_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='章节表';
CREATE TABLE `book_comment` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '评论ID',
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `chapter_id` bigint unsigned DEFAULT NULL COMMENT '章节ID；NULL=书评，非NULL=章评',
  `user_id` bigint unsigned NOT NULL COMMENT '评论人',
  `parent_id` bigint unsigned DEFAULT NULL COMMENT '父评论ID，NULL=主楼；仅支持一层回复',
  `content` varchar(500) NOT NULL COMMENT '评论内容 1~500 字',
  `like_count` int unsigned NOT NULL DEFAULT '0' COMMENT '点赞数',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1正常 0待审核 2已隐藏',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_book_list` (`book_id`,`chapter_id`,`status`,`created_at`),
  KEY `idx_user` (`user_id`),
  KEY `idx_parent` (`parent_id`),
  KEY `fk_cmt_chapter` (`chapter_id`),
  CONSTRAINT `fk_cmt_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cmt_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cmt_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='评论表';
CREATE TABLE `book_daily_stat` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `stat_date` date NOT NULL COMMENT '统计日期',
  `clicks` int unsigned NOT NULL DEFAULT '0' COMMENT '当日点击',
  `collects` int unsigned NOT NULL DEFAULT '0' COMMENT '当日收藏',
  `recommendations` int unsigned NOT NULL DEFAULT '0' COMMENT '当日投喂西瓜',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_book_date` (`book_id`,`stat_date`),
  KEY `idx_date` (`stat_date`),
  CONSTRAINT `fk_stat_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍每日统计（周榜/月榜数据源）';
CREATE TABLE `book_purchase` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `book_id` bigint unsigned NOT NULL,
  `coin` int unsigned NOT NULL COMMENT '实际支付软妹币',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_book` (`user_id`,`book_id`),
  KEY `idx_book` (`book_id`),
  CONSTRAINT `fk_purchase_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_purchase_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍购买记录';
CREATE TABLE `book_tag` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT '标签ID',
  `name` varchar(32) NOT NULL COMMENT '标签名',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='标签表';
CREATE TABLE `book_tag_rel` (
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `tag_id` int unsigned NOT NULL COMMENT '标签ID',
  PRIMARY KEY (`book_id`,`tag_id`),
  KEY `idx_tag` (`tag_id`),
  CONSTRAINT `fk_rel_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_rel_tag` FOREIGN KEY (`tag_id`) REFERENCES `book_tag` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='书籍标签关联表';
CREATE TABLE `book_vote` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint unsigned NOT NULL COMMENT '投票用户',
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `vote_type` tinyint NOT NULL DEFAULT '1' COMMENT '1推荐票 2月票',
  `vote_month` char(7) NOT NULL COMMENT '投票月份 YYYY-MM',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_book_type_month` (`user_id`,`book_id`,`vote_type`,`vote_month`),
  KEY `idx_book_month` (`book_id`,`vote_month`,`vote_type`),
  CONSTRAINT `fk_vote_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_vote_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='投票表';
CREATE TABLE `book_watermelon_log` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `book_id` bigint unsigned NOT NULL,
  `count` int unsigned NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_book` (`book_id`),
  KEY `idx_user` (`user_id`,`created_at`),
  CONSTRAINT `fk_wm_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_wm_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='投喂西瓜流水';
CREATE TABLE `chapter_purchase` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `book_id` bigint unsigned NOT NULL,
  `chapter_id` bigint unsigned NOT NULL,
  `coin` int unsigned NOT NULL COMMENT '本章实付软妹币',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_chapter` (`user_id`,`chapter_id`),
  KEY `idx_user_book` (`user_id`,`book_id`),
  KEY `fk_cp_book` (`book_id`),
  KEY `fk_cp_chapter` (`chapter_id`),
  CONSTRAINT `fk_cp_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cp_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_cp_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='按章购买记录';
CREATE TABLE `content_report` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `target_type` varchar(20) NOT NULL COMMENT '举报对象类型：book_comment / paragraph_comment',
  `target_id` bigint unsigned NOT NULL COMMENT '举报对象ID',
  `reporter_id` bigint unsigned NOT NULL COMMENT '举报人',
  `reason` varchar(200) NOT NULL DEFAULT '' COMMENT '举报理由',
  `detail` varchar(300) NOT NULL DEFAULT '' COMMENT '补充说明',
  `status` tinyint NOT NULL DEFAULT '0' COMMENT '0待处理 1已忽略 2已处理（内容已隐藏）',
  `handled_by` bigint unsigned DEFAULT NULL COMMENT '处理人',
  `handled_at` datetime DEFAULT NULL COMMENT '处理时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_target_reporter` (`target_type`,`target_id`,`reporter_id`),
  KEY `idx_status` (`status`,`created_at`),
  KEY `idx_target` (`target_type`,`target_id`),
  KEY `fk_report_user` (`reporter_id`),
  CONSTRAINT `fk_report_user` FOREIGN KEY (`reporter_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='内容举报';
CREATE TABLE `paragraph_comment` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `book_id` bigint unsigned NOT NULL,
  `parent_id` bigint unsigned DEFAULT NULL COMMENT '父间贴ID，NULL 为顶层',
  `chapter_id` bigint unsigned NOT NULL,
  `paragraph_index` int unsigned NOT NULL COMMENT '段落序号，从 0 开始',
  `user_id` bigint unsigned NOT NULL,
  `content` varchar(300) NOT NULL,
  `like_count` int unsigned NOT NULL DEFAULT '0',
  `dislike_count` int unsigned NOT NULL DEFAULT '0',
  `report_count` int unsigned NOT NULL DEFAULT '0',
  `reply_count` int unsigned NOT NULL DEFAULT '0' COMMENT '回复数',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1正常 0已隐藏',
  `audit_status` tinyint NOT NULL DEFAULT '0' COMMENT '0待审核 1已通过 2已驳回',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_para` (`chapter_id`,`paragraph_index`,`status`,`created_at`),
  KEY `idx_book` (`book_id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_parent` (`parent_id`),
  CONSTRAINT `fk_pc_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pc_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pc_parent` FOREIGN KEY (`parent_id`) REFERENCES `paragraph_comment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pc_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='间贴（段落评论）';
CREATE TABLE `paragraph_reaction` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `comment_id` bigint unsigned NOT NULL,
  `user_id` bigint unsigned NOT NULL,
  `reaction` tinyint NOT NULL COMMENT '1赞 2踩 3举报',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_comment_user` (`comment_id`,`user_id`),
  KEY `fk_pr_user` (`user_id`),
  CONSTRAINT `fk_pr_comment` FOREIGN KEY (`comment_id`) REFERENCES `paragraph_comment` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_pr_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='间贴反应';
CREATE TABLE `reading_history` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID',
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `chapter_id` bigint unsigned NOT NULL COMMENT '最后阅读章节ID',
  `chapter_no` int unsigned NOT NULL DEFAULT '0' COMMENT '最后阅读章节序号（冗余，便于展示）',
  `progress` tinyint unsigned NOT NULL DEFAULT '0' COMMENT '章内进度百分比 0~100',
  `read_count` int unsigned NOT NULL DEFAULT '1' COMMENT '累计阅读次数',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_book` (`user_id`,`book_id`),
  KEY `idx_user_time` (`user_id`,`updated_at`),
  KEY `fk_hist_book` (`book_id`),
  KEY `fk_hist_chapter` (`chapter_id`),
  CONSTRAINT `fk_hist_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_hist_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `book_chapter` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_hist_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='阅读进度表';
CREATE TABLE `recharge_order` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `order_no` varchar(32) NOT NULL,
  `user_id` bigint unsigned NOT NULL,
  `amount_fen` int unsigned NOT NULL,
  `coin` int unsigned NOT NULL,
  `status` tinyint NOT NULL DEFAULT '0',
  `remark` varchar(200) NOT NULL DEFAULT '',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `paid_at` datetime DEFAULT NULL,
  `confirmed_by` bigint unsigned DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_order_no` (`order_no`),
  KEY `idx_user_status` (`user_id`,`status`,`created_at`),
  KEY `idx_status` (`status`,`created_at`),
  CONSTRAINT `fk_order_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='充值订单表';
CREATE TABLE `sensitive_word` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `word` varchar(50) NOT NULL COMMENT '敏感词',
  `level` varchar(10) NOT NULL DEFAULT 'review' COMMENT 'block直接拦截 review转人工',
  `category` varchar(20) NOT NULL DEFAULT '其他' COMMENT '广告/辱骂/违禁/其他',
  `is_active` tinyint NOT NULL DEFAULT '1' COMMENT '1启用 0停用',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_word` (`word`),
  KEY `idx_level` (`level`,`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='敏感词库';
CREATE TABLE `site_notice` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `title` varchar(120) NOT NULL COMMENT '标题',
  `content` varchar(500) NOT NULL DEFAULT '' COMMENT '正文',
  `cover` varchar(200) NOT NULL DEFAULT '' COMMENT '封面图URL',
  `category` varchar(20) NOT NULL DEFAULT '公告' COMMENT '分类：公告/活动/更新',
  `is_top` tinyint NOT NULL DEFAULT '0' COMMENT '0普通 1置顶',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1显示 0隐藏',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_list` (`status`,`is_top`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站点公告';
CREATE TABLE `sys_user` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(32) NOT NULL COMMENT '登录名，唯一，3~20字符',
  `password_hash` varchar(255) NOT NULL COMMENT 'PBKDF2-SHA256 哈希，格式 pbkdf2_sha256$iter$salt$hash',
  `nickname` varchar(32) NOT NULL DEFAULT '' COMMENT '昵称，为空时回退 username',
  `email` varchar(128) DEFAULT NULL COMMENT '邮箱，可空',
  `avatar` varchar(255) NOT NULL DEFAULT '' COMMENT '头像地址',
  `bio` varchar(255) NOT NULL DEFAULT '' COMMENT '个人简介',
  `coin` int unsigned NOT NULL DEFAULT '0' COMMENT '软妹币余额（充值货币）',
  `watermelon` int unsigned NOT NULL DEFAULT '0' COMMENT '西瓜（签到积分）',
  `role` enum('reader','author','admin') NOT NULL DEFAULT 'reader' COMMENT '角色',
  `status` tinyint NOT NULL DEFAULT '1' COMMENT '1正常 0禁用',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  UNIQUE KEY `uk_email` (`email`),
  KEY `idx_role_status` (`role`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户表';
CREATE TABLE `user_bookshelf` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint unsigned NOT NULL COMMENT '用户ID',
  `book_id` bigint unsigned NOT NULL COMMENT '书籍ID',
  `is_top` tinyint NOT NULL DEFAULT '0' COMMENT '1=置顶',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_book` (`user_id`,`book_id`),
  KEY `idx_user_top` (`user_id`,`is_top`,`created_at`),
  KEY `fk_shelf_book` (`book_id`),
  CONSTRAINT `fk_shelf_book` FOREIGN KEY (`book_id`) REFERENCES `book` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_shelf_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='用户书架表';
CREATE TABLE `user_notice` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` bigint unsigned NOT NULL COMMENT '接收人',
  `type` varchar(20) NOT NULL DEFAULT 'system' COMMENT 'audit审核 shelf上架 report举报 system系统',
  `title` varchar(150) NOT NULL COMMENT '标题',
  `content` varchar(500) NOT NULL DEFAULT '' COMMENT '正文',
  `link` varchar(200) NOT NULL DEFAULT '' COMMENT '站内跳转地址',
  `is_read` tinyint NOT NULL DEFAULT '0' COMMENT '0未读 1已读',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_read` (`user_id`,`is_read`,`created_at`),
  CONSTRAINT `fk_notice_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='站内通知';
CREATE TABLE `user_sign_in` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `sign_date` date NOT NULL,
  `reward` int unsigned NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_date` (`user_id`,`sign_date`),
  CONSTRAINT `fk_sign_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='签到记录表';

-- 全部表建完后再打开外键检查（建表期间保持关闭，避免前向引用失败）
SET FOREIGN_KEY_CHECKS = 1;
