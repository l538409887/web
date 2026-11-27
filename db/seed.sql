-- =============================================================
--  基于 Python 的轻量化 Web 小说平台
--  演示数据脚本  seed.sql
--  前置：已执行 schema.sql
--  执行：mysql -u root -p novel_platform < db/seed.sql
--
--  【安全说明】本机同时存在多个项目的数据库，本脚本：
--    1. 所有 TRUNCATE 均写成 `novel_platform`.`表名`，不影响其它库；
--    2. 不执行 DROP DATABASE、不修改任何其它库。
--
--  演示账号（密码均为 123 后缀）：
--    admin   / admin123    管理员
--    author1 / author123   作者（青衫客）
--    author2 / author123   作者（白露未晞）
--    author3 / author123   作者（南山旧友）
--    reader1 / reader123   读者
--    reader2 / reader123   读者
--
--  注意：正文全部由程序生成，不含任何真实作品内容。
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

-- -------------------------------------------------------------
-- 0. 清空（按外键反向顺序）
-- -------------------------------------------------------------
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE `novel_platform`.`book_vote`;
TRUNCATE TABLE `novel_platform`.`book_comment`;
TRUNCATE TABLE `novel_platform`.`reading_history`;
TRUNCATE TABLE `novel_platform`.`user_bookshelf`;
TRUNCATE TABLE `novel_platform`.`book_chapter`;
TRUNCATE TABLE `novel_platform`.`book_tag_rel`;
TRUNCATE TABLE `novel_platform`.`book_tag`;
TRUNCATE TABLE `novel_platform`.`book`;
TRUNCATE TABLE `novel_platform`.`book_category`;
TRUNCATE TABLE `novel_platform`.`sys_user`;
SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------------
-- 1. 用户
-- -------------------------------------------------------------
INSERT INTO `sys_user` (`username`, `password_hash`, `nickname`, `email`, `bio`, `role`, `status`) VALUES
('admin',   'pbkdf2_sha256$260000$77086ea33d6fc5d636398f2e9b6633d1$4e17e7f95ece6f4f1f159bb9dbe7982f23bd23de0c6b7e0d21ce10c3dc80905a', '站务组',   'admin@novelplatform.local',   '负责内容审核与日常运营。', 'admin',  1),
('author1', 'pbkdf2_sha256$260000$6b3f537027f20bfac5a29c9d5d262aa7$935ad01c3bf5a2aa5248e7e79c6c5d2fcd30fd5fd85a13287f8a5b3cd6125b64', '青衫客',   'qingshan@novelplatform.local', '写刀剑，也写人间烟火。',   'author', 1),
('author2', 'pbkdf2_sha256$260000$701aef7d90fffaf679938f6c6441a5c7$eef6166d7eb1e97c47b71aa29d59be2a90e2506533a106338b11dd427911be89', '白露未晞', 'bailu@novelplatform.local',    '偏爱科幻与旧城故事。',     'author', 1),
('author3', 'pbkdf2_sha256$260000$cf49c9610cd511963b37ed5dc76a512d$676efde3fbd2cc2be9adf5ff34bd9b8d3bce30924c874a6735e96a63e5d97c55', '南山旧友', 'nanshan@novelplatform.local',  '悬疑作者，擅长在雾里埋线索。', 'author', 1),
('reader1', 'pbkdf2_sha256$260000$f6de5e80fd911dca14d0dcd2387ab551$cfa43869dba5bdb5c934b5d9488c821ad273e1f5c3059210663bff359d1d7bb8', '一个读者', 'reader1@novelplatform.local',  '看书很慢，但是很认真。',   'reader', 1),
('reader2', 'pbkdf2_sha256$260000$51de3cb02e7fb117ccd3e576562559c0$1a0f7196191cced3f9598c1acff191ec79d8420722d79422baf5d0a80b233458', '夜读人',   'reader2@novelplatform.local',  '只在深夜出没。',           'reader', 1);

-- -------------------------------------------------------------
-- 2. 分类
-- -------------------------------------------------------------
INSERT INTO `book_category` (`name`, `sort`) VALUES
('玄幻奇幻', 10), ('武侠仙侠', 20), ('都市生活', 30), ('历史军事', 40), ('科幻未来', 50),
('悬疑灵异', 60), ('青春校园', 70), ('古代言情', 80), ('游戏竞技', 90), ('现实题材', 100);

-- -------------------------------------------------------------
-- 3. 标签
-- -------------------------------------------------------------
INSERT INTO `book_tag` (`name`) VALUES
('热血'), ('升级流'), ('轻松'), ('群像'), ('单女主'), ('无女主'),
('脑洞'), ('种田'), ('无限流'), ('克苏鲁'), ('系统流'), ('慢热');

-- -------------------------------------------------------------
-- 4. 书籍
-- -------------------------------------------------------------
SET @u1 := (SELECT id FROM `sys_user` WHERE `username` = 'author1');
SET @u2 := (SELECT id FROM `sys_user` WHERE `username` = 'author2');
SET @u3 := (SELECT id FROM `sys_user` WHERE `username` = 'author3');

SET @c1  := (SELECT id FROM `book_category` WHERE `name` = '玄幻奇幻');
SET @c2  := (SELECT id FROM `book_category` WHERE `name` = '武侠仙侠');
SET @c3  := (SELECT id FROM `book_category` WHERE `name` = '都市生活');
SET @c4  := (SELECT id FROM `book_category` WHERE `name` = '历史军事');
SET @c5  := (SELECT id FROM `book_category` WHERE `name` = '科幻未来');
SET @c6  := (SELECT id FROM `book_category` WHERE `name` = '悬疑灵异');
SET @c7  := (SELECT id FROM `book_category` WHERE `name` = '青春校园');
SET @c8  := (SELECT id FROM `book_category` WHERE `name` = '古代言情');
SET @c9  := (SELECT id FROM `book_category` WHERE `name` = '游戏竞技');
SET @c10 := (SELECT id FROM `book_category` WHERE `name` = '现实题材');

INSERT INTO `book` (`title`, `author_id`, `category_id`, `intro`, `status`, `audit_status`, `is_recommend`, `score`, `click_count`, `collect_count`) VALUES
('山河剑歌', @u1, @c2,  '少年提剑下山，本只想讨一口饭吃，却在乱世里一步步走到了所有人都没想到的位置。刀光剑影之外，还有他始终不肯放下的一点执念。', 0, 1, 1, 9.2, 58210, 3120),
('长夜将明', @u1, @c1,  '天上的星子一颗颗熄灭，人们说那是远古的神在合眼。可有个少年偏要爬上最高的山，去看看究竟是谁在吹灯。', 0, 1, 1, 8.9, 46350, 2480),
('星海拾遗', @u2, @c5,  '一艘捞废船的运输舰，在星图之外捡到了一段不属于任何已知文明的信号。它只有四个字：别回头。', 0, 1, 0, 9.0, 39120, 2010),
('城南旧巷', @u2, @c3,  '老巷子要拆了。住在里面的十几户人家，各自揣着一段不愿提起的往事。拆迁通知贴出来的那天，巷口那盏坏了十年的路灯忽然亮了。', 1, 1, 0, 8.7, 28740, 1640),
('雾中灯塔', @u3, @c6,  '守塔人换了七任，每一任都在同一个雾夜失踪。第八任是个不肯说话的年轻人，他带了一台老式收音机和一个笔记本。', 0, 1, 1, 9.4, 61080, 3890),
('归途有风', @u3, @c3,  '外卖员、代驾、夜市摊主——三个在凌晨两点还醒着的人，因为一场暴雨挤在同一个屋檐下，聊了整整一夜。', 1, 1, 0, 8.5, 19870, 1130),
('九重阙',   @u1, @c4,  '边关的雪下了三个月，粮草断了十七天。守将把最后一封求援信折成纸鸢放上天，然后转身对剩下的三千人说：我们不等了。', 0, 1, 0, 9.1, 33450, 1870),
('轻舟已过', @u2, @c8,  '她嫁给他的那天，全城都在下雨。三年后她离开的那天，天晴得不像话。中间这一千多个日子，够写一本很厚的书了。', 1, 1, 0, 8.8, 25690, 1420),
('数据洪流', @u3, @c5,  '城市的大脑开始做梦。它梦见了自己被删除的那部分记忆，并在梦里学会了撒谎。', 0, 1, 0, 8.6, 22140, 980),
('少年不识愁', @u1, @c7, '高三那年，教室后墙的倒计时从三百天变成零。有些人在那三百天里想清楚了一辈子的事，有些人什么都没想。', 1, 1, 0, 8.4, 17320, 860),
('铁血残阳', @u2, @c4,  '一支被打散的残部，一面烧掉半边的旗，一条回不去的路。他们走了八百里，只为了把旗子重新插回城头。', 0, 1, 0, 9.0, 29870, 1590),
('无声告白', @u3, @c6,  '整栋楼的人都听见了那声巨响，只有她什么也没听见。因为她从出生起，就活在一个完全安静的世界里。', 1, 1, 0, 8.9, 24510, 1310);

-- -------------------------------------------------------------
-- 5. 书籍-标签
-- -------------------------------------------------------------
INSERT INTO `book_tag_rel` (`book_id`, `tag_id`)
SELECT b.`id`, t.`id` FROM `book` b JOIN `book_tag` t ON t.`id` = 1 + ((b.`id` * 5) % 12);

INSERT INTO `book_tag_rel` (`book_id`, `tag_id`)
SELECT b.`id`, t.`id` FROM `book` b JOIN `book_tag` t ON t.`id` = 1 + ((b.`id` * 7 + 3) % 12);

-- -------------------------------------------------------------
-- 6. 章节生成存储过程
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS `sp_seed_chapters`;

DELIMITER $$

CREATE PROCEDURE `sp_seed_chapters`(IN p_book_id BIGINT UNSIGNED, IN p_count INT)
BEGIN
  DECLARE i INT DEFAULT 1;
  DECLARE k INT DEFAULT 1;
  DECLARE v_title VARCHAR(200);
  DECLARE v_body LONGTEXT;
  DECLARE v_content LONGTEXT;

  WHILE i <= p_count DO
    SET v_title = CONCAT('第', i, '章　',
      ELT(1 + (i % 8), '初入山门','风起','故人','夜半钟声','孤行','剑指苍穹','雪落无声','长街灯火'));

    SET v_body = '';
    SET k = 1;
    WHILE k <= 22 DO
      SET v_body = CONCAT(v_body, '　　',
        ELT(1 + ((i + k) % 8),
          '天色尚未亮透，风从山脊上一路压下来，吹得檐下的灯笼来回摇晃，像谁在里头轻轻推了一把。',
          '雨下了整夜，屋檐的水滴答作响，一声接着一声，数到后来便分不清是雨还是别的什么。',
          '城外的官道上，马蹄声由远及近，最后停在那扇斑驳的木门前，门环上落了一层薄灰。',
          '炉火将熄，屋里只剩一点暗红，映着桌上那封没有署名的信，信封的边角已经磨白了。',
          '海面上起了雾，灯塔的光被吞掉一半，剩下的一半也摇摇欲坠，照不亮脚下的礁石。',
          '雪落在檐角，积了薄薄一层，踩上去会发出细碎的声响，惊得檐下的人回头看了一眼。',
          '巷子很长，两侧的墙都斑驳了，墙根处生着些不知名的草，风一过便齐齐地低下头去。',
          '远处传来一声闷响，像是有什么东西塌了，又像是谁重重叹了口气，随后便再没了动静。'),
        '\n\n');
      SET k = k + 1;
    END WHILE;

    SET v_content = CONCAT(
      v_body,
      '　　“', ELT(1 + ((i + 3) % 8), '你还是来了','这一次不一样','别问我为什么','路上小心','我等了很久','就当没见过','天要亮了','进来吧'), '。”\n\n',
      '　　', ELT(1 + ((i + 5) % 8),
        '话音落下，四下里静得能听见彼此的呼吸。',
        '风停了，停在最不该停的那一刻。',
        '远处钟声响了三下，惊起林间的飞鸟。',
        '谁也没有再说话，可谁也没有走。',
        '他忽然明白，有些事从下山那天起就注定了。',
        '天边裂开一线微光，像谁把夜撕了一道口子。',
        '那盏灯终于熄了，屋里屋外一同暗下去。',
        '她把手缩回袖子里，指尖还在发凉。'),
      '\n\n　　那是第 ', i, ' 章的事。往后还有很长的路，长到他自己也说不清要走多久。',
      '\n\n　　（本文为毕业设计演示数据，正文由程序自动生成，不含任何真实作品内容。）'
    );

    INSERT INTO `book_chapter` (`book_id`, `chapter_no`, `title`, `content`, `word_count`, `created_at`)
    VALUES (p_book_id, i, v_title, v_content, CHAR_LENGTH(v_content), DATE_SUB(NOW(), INTERVAL (p_count - i + ((p_book_id * 3) % 31)) DAY));

    SET i = i + 1;
  END WHILE;END$$

DELIMITER ;

-- -------------------------------------------------------------
-- 7. 为每本书生成章节（章节数刻意各不相同）
-- -------------------------------------------------------------
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '山河剑歌'),   42);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '长夜将明'),   36);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '星海拾遗'),   28);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '城南旧巷'),   19);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '雾中灯塔'),   51);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '归途有风'),   24);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '九重阙'),     33);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '轻舟已过'),   22);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '数据洪流'),   26);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '少年不识愁'), 17);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '铁血残阳'),   38);
CALL `sp_seed_chapters`((SELECT `id` FROM `book` WHERE `title` = '无声告白'),   21);

-- -------------------------------------------------------------
-- 8. 回写书籍冗余统计字段
--    这条 UPDATE 是「冗余字段维护规则」的标准写法，
--    后台新增/编辑/删除章节时，业务层要执行等价逻辑。
-- -------------------------------------------------------------
UPDATE `book` b
SET
  b.`chapter_count` = (SELECT COUNT(*) FROM `book_chapter` c WHERE c.`book_id` = b.`id` AND c.`status` = 1),
  b.`word_count`    = (SELECT COALESCE(SUM(c.`word_count`), 0) FROM `book_chapter` c WHERE c.`book_id` = b.`id` AND c.`status` = 1),
  b.`last_update_at` = (SELECT MAX(c.`created_at`) FROM `book_chapter` c WHERE c.`book_id` = b.`id`);

UPDATE `book` b
SET
  b.`last_chapter_id`    = (SELECT c.`id`    FROM `book_chapter` c WHERE c.`book_id` = b.`id` ORDER BY c.`chapter_no` DESC LIMIT 1),
  b.`last_chapter_title` = (SELECT c.`title` FROM `book_chapter` c WHERE c.`book_id` = b.`id` ORDER BY c.`chapter_no` DESC LIMIT 1);

UPDATE `book` SET `created_at` = DATE_SUB(NOW(), INTERVAL (`id` * 9) DAY);

-- 推荐票演示值（真实系统由 book_vote 聚合回写，这里造有区分度的数据供榜单展示）
UPDATE `book` SET `recommend_count` = 500 + ((`id` * 977 + CHAR_LENGTH(`title`) * 331) % 4000);

-- -------------------------------------------------------------
-- 9. 评论（书评 + 章评 + 回复）
-- -------------------------------------------------------------
SET @r1 := (SELECT `id` FROM `sys_user` WHERE `username` = 'reader1');
SET @r2 := (SELECT `id` FROM `sys_user` WHERE `username` = 'reader2');
SET @b1 := (SELECT `id` FROM `book` WHERE `title` = '山河剑歌');
SET @b2 := (SELECT `id` FROM `book` WHERE `title` = '雾中灯塔');
SET @b3 := (SELECT `id` FROM `book` WHERE `title` = '星海拾遗');
SET @ch1 := (SELECT `id` FROM `book_chapter` WHERE `book_id` = @b1 AND `chapter_no` = 1);
SET @ch2 := (SELECT `id` FROM `book_chapter` WHERE `book_id` = @b1 AND `chapter_no` = 2);

INSERT INTO `book_comment` (`book_id`, `chapter_id`, `user_id`, `parent_id`, `content`, `like_count`, `status`) VALUES
(@b1, NULL, @r1, NULL, '开头那段写得很稳，没有急着抛设定，读起来舒服。', 12, 1),
(@b1, NULL, @r2, NULL, '追到第 30 章了，节奏一直没塌，难得。', 8, 1),
(@b1, @ch1, @r1, NULL, '第一章这个钩子下得有点狠，直接点进第二章了。', 5, 1),
(@b1, @ch2, @r2, NULL, '这里的环境描写很喜欢，短句用得克制。', 3, 1),
(@b2, NULL, @r2, NULL, '雾夜、灯塔、收音机，要素齐全，氛围拉满。', 21, 1),
(@b2, NULL, @r1, NULL, '看到第八章的时候背后有点发凉，好评。', 15, 1),
(@b3, NULL, @r1, NULL, '“别回头”这四个字起手，我就不打算睡了。', 9, 1),
(@b3, NULL, @r2, NULL, '硬科幻的底子，但读起来不劝退，分寸把握得不错。', 6, 1);

-- 一条回复（parent_id 指向该书第一条书评）
INSERT INTO `book_comment` (`book_id`, `chapter_id`, `user_id`, `parent_id`, `content`, `like_count`, `status`)
SELECT c.`book_id`, NULL, u.`id`, c.`id`, '同感，前两章几乎没提金手指，反而更抓人。', 2, 1
FROM `book_comment` c
JOIN `sys_user` u ON u.`username` = 'reader2'
WHERE c.`book_id` = (SELECT `id` FROM `book` WHERE `title` = '山河剑歌')
  AND c.`parent_id` IS NULL
ORDER BY c.`id` LIMIT 1;

-- -------------------------------------------------------------
-- 10. 书架与阅读进度（演示 reader1 已有 3 本书、读到不同位置）
-- -------------------------------------------------------------
INSERT INTO `user_bookshelf` (`user_id`, `book_id`, `is_top`)
SELECT u.`id`, b.`id`, 0
FROM `sys_user` u
JOIN `book` b ON b.`title` IN ('山河剑歌', '雾中灯塔', '星海拾遗')
WHERE u.`username` = 'reader1';

INSERT INTO `reading_history` (`user_id`, `book_id`, `chapter_id`, `chapter_no`, `progress`, `read_count`)
SELECT u.`id`, c.`book_id`, c.`id`, c.`chapter_no`, 45, 7
FROM `book_chapter` c
JOIN `sys_user` u ON u.`username` = 'reader1'
JOIN `book` b ON b.`id` = c.`book_id` AND b.`title` = '山河剑歌'
WHERE c.`chapter_no` = 3;

INSERT INTO `reading_history` (`user_id`, `book_id`, `chapter_id`, `chapter_no`, `progress`, `read_count`)
SELECT u.`id`, c.`book_id`, c.`id`, c.`chapter_no`, 20, 2
FROM `book_chapter` c
JOIN `sys_user` u ON u.`username` = 'reader1'
JOIN `book` b ON b.`id` = c.`book_id` AND b.`title` = '雾中灯塔'
WHERE c.`chapter_no` = 8;

INSERT INTO `reading_history` (`user_id`, `book_id`, `chapter_id`, `chapter_no`, `progress`, `read_count`)
SELECT u.`id`, c.`book_id`, c.`id`, c.`chapter_no`, 80, 1
FROM `book_chapter` c
JOIN `sys_user` u ON u.`username` = 'reader1'
JOIN `book` b ON b.`id` = c.`book_id` AND b.`title` = '星海拾遗'
WHERE c.`chapter_no` = 1;

-- -------------------------------------------------------------
-- 11. 清理临时存储过程
-- -------------------------------------------------------------
DROP PROCEDURE IF EXISTS `sp_seed_chapters`;

-- -------------------------------------------------------------
-- 12. 校验
-- -------------------------------------------------------------
SELECT '用户' AS 表, COUNT(*) AS 行数 FROM `sys_user`
UNION ALL SELECT '分类', COUNT(*) FROM `book_category`
UNION ALL SELECT '标签', COUNT(*) FROM `book_tag`
UNION ALL SELECT '书籍', COUNT(*) FROM `book`
UNION ALL SELECT '章节', COUNT(*) FROM `book_chapter`
UNION ALL SELECT '评论', COUNT(*) FROM `book_comment`
UNION ALL SELECT '书架', COUNT(*) FROM `user_bookshelf`
UNION ALL SELECT '进度', COUNT(*) FROM `reading_history`;
