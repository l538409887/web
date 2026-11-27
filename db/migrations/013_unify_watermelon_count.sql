USE novel_platform;

-- 统一「投喂西瓜」计数口径：
--   watermelon_count 是真实业务字段（投喂时 +n）
--   recommend_count  是早期种子数据字段，从未被业务代码维护
-- 两列各记一套导致「投喂了但榜不变」，这里把历史值并入 watermelon_count。
UPDATE book
   SET watermelon_count = recommend_count
 WHERE recommend_count > watermelon_count;

ALTER TABLE `book`
  MODIFY COLUMN `recommend_count` INT NOT NULL DEFAULT 0
  COMMENT '已废弃：历史推荐数，统一用 watermelon_count';