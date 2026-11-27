-- =============================================================
--  演示数据补充：为首页三个书区补足书目
--
--  背景：seed.sql 只有 12 本书，首页被「好书精选 4 + 精品力荐 12」
--  吃光后「新秀小说」会空白，所以补 10 本新上架作品。
--
--  执行：mysql -u root -p novel_platform < db/demo_extra_books.sql
--  注意：本脚本不具备幂等性，重复执行会重复插入，请只跑一次。
-- =============================================================

USE `novel_platform`;
SET NAMES utf8mb4;

DROP PROCEDURE IF EXISTS sp_add_demo_book;
DELIMITER $$
CREATE PROCEDURE sp_add_demo_book(
  IN p_title   VARCHAR(100),
  IN p_author  BIGINT,
  IN p_cat     BIGINT,
  IN p_intro   VARCHAR(255),
  IN p_chapters INT,
  IN p_days    INT
)
BEGIN
  DECLARE v_book BIGINT;
  DECLARE i INT DEFAULT 1;
  DECLARE body LONGTEXT;

  INSERT INTO book(title, author_id, category_id, intro, cover, status, audit_status,
                   click_count, collect_count, recommend_count, score,
                   chapter_count, word_count, created_at, last_update_at)
  VALUES (p_title, p_author, p_cat, p_intro, '', 0, 1,
          300 + p_days * 15, 0, 0, 8.0,
          0, 0, DATE_SUB(NOW(), INTERVAL p_days DAY), DATE_SUB(NOW(), INTERVAL p_days DAY));
  SET v_book = LAST_INSERT_ID();

  WHILE i <= p_chapters DO
    SET body = CONCAT('　　第 ', i, ' 章。', p_intro,
      REPEAT('\n\n　　风从窗缝里钻进来，带着一点潮气。他把手里的灯往前举了举，光落在墙上，照出一片斑驳的影子。', 15));
    INSERT INTO book_chapter(book_id, chapter_no, title, content, word_count, status, created_at)
    VALUES (v_book, i,
            CONCAT('第', i, '章　', ELT(1 + (i % 6), '起风了', '旧信', '夜路', '雨后', '远客', '灯下')),
            body, CHAR_LENGTH(body), 1,
            DATE_SUB(NOW(), INTERVAL (p_days + p_chapters - i) DAY));
    SET i = i + 1;
  END WHILE;

  UPDATE book b SET
    b.chapter_count      = (SELECT COUNT(*) FROM book_chapter c WHERE c.book_id = b.id AND c.status = 1),
    b.word_count         = (SELECT COALESCE(SUM(c.word_count), 0) FROM book_chapter c WHERE c.book_id = b.id AND c.status = 1),
    b.last_update_at     = (SELECT MAX(c.created_at) FROM book_chapter c WHERE c.book_id = b.id),
    b.last_chapter_id    = (SELECT c.id FROM book_chapter c WHERE c.book_id = b.id ORDER BY c.chapter_no DESC LIMIT 1),
    b.last_chapter_title = (SELECT c.title FROM book_chapter c WHERE c.book_id = b.id ORDER BY c.chapter_no DESC LIMIT 1)
  WHERE b.id = v_book;
END$$
DELIMITER ;

CALL sp_add_demo_book('归墟纪年', 2, 1,  '海图之外没有归途，只有一代代人把名字刻在礁石上。', 12, 2);
CALL sp_add_demo_book('剑阁闻铃', 2, 8,  '剑阁的铃一响，山下就有人要死。这次响的是他的名字。', 10, 1);
CALL sp_add_demo_book('星环之下', 3, 5,  '在星环的阴影里，所有坐标都是谎话，只有心跳是准的。', 14, 3);
CALL sp_add_demo_book('长夜行舟', 3, 2,  '摆渡人不问来处，只问一句：你要去的那岸，还回得来吗？', 9, 4);
CALL sp_add_demo_book('春日迟迟', 4, 10, '她把喜欢藏了七年，藏在每一封没寄出去的信里。', 11, 5);
CALL sp_add_demo_book('无声之城', 4, 9,  '整座城市在同一分钟失声，只有她听见了那一声求救。', 8, 6);
CALL sp_add_demo_book('白露为霜', 2, 7,  '多年前欠下的一句承诺，终于在霜降那天有人来讨。', 13, 7);
CALL sp_add_demo_book('山海遗事', 3, 6,  '怪物不是从山里来的，是从人心里长出来的。', 10, 8);
CALL sp_add_demo_book('雾外青山', 4, 8,  '他离开那天山里起了雾，回来时雾还没散。', 12, 9);
CALL sp_add_demo_book('第七个夏天', 2, 10, '每年夏天都有一个人消失，今年轮到她了。', 9, 10);

DROP PROCEDURE sp_add_demo_book;

-- 付费作品的整本价随字数重算
UPDATE book SET price_coin = CEIL(word_count * 5 / 1000) WHERE is_paid = 1;
