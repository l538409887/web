-- =============================================================
--  应用数据库账号初始化  00_create_user.sql
--  用途：为应用创建最小权限账号，避免用 root 连库
--  执行：由 root 执行一次即可，mysql -u root -p < db/00_create_user.sql
--
--  权限说明：
--    SELECT / INSERT / UPDATE / DELETE  —— 应用日常所需
--    不给 DROP / ALTER / GRANT          —— 防止误删表、误改结构
--    只授予 novel_platform.*            —— 对其它项目库零权限
--
--  注意：真实密码不要写在这个文件里（会进 Git）。
--        实际密码保存在 backend/.env 的 DATABASE_URL 中。
-- =============================================================

CREATE USER IF NOT EXISTS 'novel_app'@'localhost' IDENTIFIED BY 'CHANGE_ME_SEE_BACKEND_ENV';
CREATE USER IF NOT EXISTS 'novel_app'@'127.0.0.1' IDENTIFIED BY 'CHANGE_ME_SEE_BACKEND_ENV';

GRANT SELECT, INSERT, UPDATE, DELETE ON `novel_platform`.* TO 'novel_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON `novel_platform`.* TO 'novel_app'@'127.0.0.1';

FLUSH PRIVILEGES;

-- 核对权限：
-- SHOW GRANTS FOR 'novel_app'@'localhost';