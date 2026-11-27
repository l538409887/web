-- =============================================================
--  创建测试库并授权（只执行一次）
--  用途：pytest 会把整个应用指向 novel_platform_test，
--        与生产库 novel_platform 完全隔离。
--
--  执行：mysql -u root -p < db/00_create_test_db.sql
--
--  注意：这里给 novel_app 授予了 DDL 权限（CREATE/DROP/ALTER/INDEX），
--        仅限测试库。生产库 novel_platform 仍然只有 DML 权限。
-- =============================================================

CREATE DATABASE IF NOT EXISTS `novel_platform_test`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES
  ON `novel_platform_test`.* TO 'novel_app'@'localhost';

FLUSH PRIVILEGES;
