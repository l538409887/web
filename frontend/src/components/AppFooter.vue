<template>
  <footer class="ft">
    <div class="container ft__inner">
      <div class="ft__cols">
        <div class="ft__col">
          <h4>关于平台</h4>
          <router-link to="/">网站首页</router-link>
          <router-link to="/search">全部作品</router-link>
          <router-link to="/rank">排行榜单</router-link>
        </div>
        <div class="ft__col">
          <h4>作者服务</h4>
          <router-link to="/author">作者后台</router-link>
          <router-link to="/author">作品管理</router-link>
          <router-link to="/user">个人中心</router-link>
        </div>
        <div class="ft__col">
          <h4>帮助中心</h4>
          <a href="#" @click.prevent>阅读说明</a>
          <a href="#" @click.prevent>常见问题</a>
          <a href="#" @click.prevent>意见反馈</a>
        </div>
        <div class="ft__col ft__col--wide">
          <h4>关于本站</h4>
          <p>
            本站为本科毕业设计作品，基于 Python + FastAPI + Vue3 实现的前后端分离小说阅读平台。
          </p>
          <p>演示数据由程序生成，不含任何真实作品内容。</p>
        </div>
      </div>

      <div class="ft__bottom">
        <span>轻量化小说平台 · 毕业设计</span>
        <span>演示环境 · 仅供学习交流</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.ft {
  margin-top: 40px;
  background: #2f2f33;
  color: #b9b9bf;
}

.ft__inner {
  padding: 36px 20px 24px;
}

.ft__cols {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 2fr;
  gap: 28px;
}

.ft__col {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ft__col h4 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
}

.ft__col a {
  font-size: 13px;
  color: #b9b9bf;
}

.ft__col a:hover {
  color: var(--c-primary-light);
}

.ft__col p {
  margin: 0;
  font-size: 12px;
  line-height: 1.9;
}

.ft__bottom {
  display: flex;
  justify-content: space-between;
  margin-top: 28px;
  padding-top: 16px;
  border-top: 1px solid #42424a;
  font-size: 12px;
  color: #8a8a92;
}

@media (max-width: 768px) {
  .ft__cols {
    grid-template-columns: 1fr 1fr;
  }
  .ft__col--wide {
    grid-column: 1 / -1;
  }
  .ft__bottom {
    flex-direction: column;
    gap: 6px;
  }
}
</style>