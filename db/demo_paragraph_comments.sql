
-- 清理残留，保证可重复执行
DELETE FROM paragraph_comment;

-- 山河剑歌（book 1）第 1~3 章的真实间贴
INSERT INTO paragraph_comment
  (book_id, chapter_id, paragraph_index, user_id, content, like_count, dislike_count, status, audit_status)
VALUES
  (1, 1, 0, 5, '开篇这句就把人抓住了。', 12, 0, 1, 1),
  (1, 1, 2, 6, '风起于青萍之末，这个意象用得真好。', 8, 1, 1, 1),
  (1, 1, 5, 2, '看到这里想起自己刚入行的时候。', 3, 0, 1, 1),
  (1, 2, 1, 6, '故人重逢这段写得克制，反而更动人。', 15, 0, 1, 1),
  (1, 2, 3, 5, '这里埋伏笔了吧？后面肯定要出事。', 6, 0, 1, 1),
  (1, 3, 0, 5, '夜半钟声这一章氛围绝了。', 9, 0, 1, 1),
  (1, 3, 4, 6, '催更催更，一口气看到这里。', 21, 0, 1, 1),
  (1, 3, 6, 3, '这段打斗写得很扎实。', 4, 1, 1, 1);

-- 雾中灯塔（book 5）第 1~2 章
INSERT INTO paragraph_comment
  (book_id, chapter_id, paragraph_index, user_id, content, like_count, dislike_count, status, audit_status)
VALUES
  (5, 126, 0, 6, '灯塔这个意象一出来就很有画面感。', 17, 0, 1, 1),
  (5, 126, 3, 5, '主角的孤独感写得很准。', 7, 0, 1, 1),
  (5, 127, 1, 5, '这段对话有点意思，两个人都在绕。', 5, 1, 1, 1),
  (5, 127, 4, 2, '节奏稍微慢了一点，但能接受。', 2, 0, 1, 1);

-- 顶层间贴的 reply_count 与实际回复数对齐（这里没有回复，保持 0）
UPDATE paragraph_comment SET reply_count = 0 WHERE parent_id IS NULL;

-- 按真实数据重算书表的间贴计数，修掉历史残留（曾有书显示 4 条但库里 0 条）
UPDATE book b
   SET b.paragraph_comment_count = (
       SELECT COUNT(*) FROM paragraph_comment p
        WHERE p.book_id = b.id AND p.parent_id IS NULL AND p.status = 1
   );