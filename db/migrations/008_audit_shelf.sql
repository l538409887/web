USE novel_platform;
SET NAMES utf8mb4;

-- ---------------------------------------------------------------
-- 一、书籍：审核四态 + 上架四态
--    audit_status: 0草稿(未提交) 1待审核 2已通过 3未通过
--    shelf_status: 0未上架     1申请中   2已上架 3上架被拒
-- ---------------------------------------------------------------
ALTER TABLE `book`
  ADD COLUMN `shelf_status` TINYINT NOT NULL DEFAULT 0 COMMENT '0未上架 1上架申请中 2已上架 3上架被拒' AFTER `audit_status`;

-- 旧语义 -> 新语义：0待审->1待审核，1通过->2已通过，2驳回->3未通过
UPDATE `book` SET `audit_status` = CASE `audit_status`
    WHEN 0 THEN 1
    WHEN 1 THEN 2
    WHEN 2 THEN 3
    ELSE 3
  END;

-- 已通过的书默认视为已上架，保证前台不空
UPDATE `book` SET `shelf_status` = 2 WHERE `audit_status` = 2;

-- ---------------------------------------------------------------
-- 二、章节：加审核态（历史章节视为已通过）
-- ---------------------------------------------------------------
ALTER TABLE `book_chapter`
  ADD COLUMN `audit_status` TINYINT NOT NULL DEFAULT 1 COMMENT '0草稿 1待审核 2已通过 3未通过' AFTER `status`;

UPDATE `book_chapter` SET `audit_status` = 2;

-- ---------------------------------------------------------------
-- 三、间贴：加审核态（先发后审，历史间贴视为已通过）
--    audit_status: 0待审核 1已通过 2已驳回（驳回后前台不展示）
-- ---------------------------------------------------------------
ALTER TABLE `paragraph_comment`
  ADD COLUMN `audit_status` TINYINT NOT NULL DEFAULT 0 COMMENT '0待审核 1已通过 2已驳回' AFTER `status`;

UPDATE `paragraph_comment` SET `audit_status` = 1;