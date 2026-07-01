<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()

const professions = [
  { name: '生化', desc: '毒液侵蚀，控场压制', key: '生化' },
  { name: '突击', desc: '高机动强火力先锋', key: '突击' },
  { name: '护卫', desc: '前排肉盾稳固防线', key: '护卫' },
  { name: '重装', desc: '重火力压制机甲', key: '重装' },
]
</script>

<template>
  <section class="hero">
    <div class="hero-glow"></div>
    <div class="hero-inner container">
      <p class="kicker">AVATAR STAR · 官方赛事</p>
      <h1 class="hero-title">百变兵团 <span>选花杯</span></h1>
      <p class="hero-sub">
        组建你的五人战队，覆盖生化 · 突击 · 护卫 · 重装四大职业，
        踏上通往冠军的对阵之路。
      </p>
      <div class="hero-cta row">
        <RouterLink v-if="auth.isAuthenticated" to="/signup" class="btn accent">立即报名</RouterLink>
        <RouterLink v-else to="/register" class="btn accent">注册并报名</RouterLink>
        <RouterLink to="/browse" class="btn ghost">查看赛事对阵</RouterLink>
      </div>
    </div>
  </section>

  <div class="container">
    <div class="grid cols-3 steps">
      <div class="card">
        <div class="step-no">01</div>
        <h3>注册账号</h3>
        <p class="muted">创建你的选手账号，一分钟即可完成。</p>
      </div>
      <div class="card">
        <div class="step-no">02</div>
        <h3>提交战队</h3>
        <p class="muted">填写队伍信息与五名正式队员及替补名单。</p>
      </div>
      <div class="card">
        <div class="step-no">03</div>
        <h3>审核晋级</h3>
        <p class="muted">通过审核后进入对阵图，逐轮争夺冠军。</p>
      </div>
    </div>

    <h2 class="section-title">四大职业</h2>
    <div class="grid cols-4 prof-grid">
      <div v-for="p in professions" :key="p.key" class="card prof-card">
        <span class="prof-tag" :class="'prof-' + p.key">
          <span class="dot" :style="{ background: `var(--prof-${p.key})` }"></span>{{ p.name }}
        </span>
        <p class="muted">{{ p.desc }}</p>
      </div>
    </div>

    <div class="panel rules">
      <h2>组队规则</h2>
      <ul>
        <li>每支战队 <strong>正式队员严格为 5 人</strong>，替补人数不限。</li>
        <li>四大职业 <strong>每种至少 1 人、至多 2 人</strong>，即 2+1+1+1 的组合。</li>
        <li>报名提交后需经 <strong>管理员审核</strong>，通过后方可出现在赛事浏览页。</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--border);
}
.hero-glow {
  position: absolute; inset: -40% -10% auto -10%; height: 140%;
  background:
    radial-gradient(600px 300px at 20% 30%, rgba(255, 122, 60, 0.35), transparent 60%),
    radial-gradient(700px 340px at 80% 20%, rgba(43, 139, 255, 0.45), transparent 60%);
  filter: blur(4px);
}
.hero-inner { position: relative; padding-top: 4.5rem; padding-bottom: 4rem; }
.kicker { letter-spacing: 3px; color: var(--primary-2); font-weight: 700; font-size: 0.8rem; margin: 0 0 0.5rem; }
.hero-title { font-size: clamp(2.4rem, 6vw, 4rem); line-height: 1.05; letter-spacing: 1px; }
.hero-title span {
  background: linear-gradient(135deg, var(--accent-2), var(--accent));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { max-width: 560px; color: var(--muted); font-size: 1.05rem; line-height: 1.6; }
.hero-cta { margin-top: 1.5rem; }

.cols-3 { grid-template-columns: repeat(3, 1fr); }
.cols-4 { grid-template-columns: repeat(4, 1fr); }
.steps { margin-top: -2rem; position: relative; z-index: 2; }
.step-no { font-size: 1.6rem; font-weight: 800; color: var(--primary-2); opacity: 0.5; }

.section-title { margin: 2.5rem 0 1rem; }
.prof-card p { margin: 0.5rem 0 0; }
.prof-tag { display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 800; font-size: 1.1rem; }
.prof-tag .dot { width: 10px; height: 10px; border-radius: 50%; }

.rules { margin-top: 2.5rem; }
.rules ul { margin: 0.5rem 0 0; padding-left: 1.2rem; line-height: 2; color: var(--text); }
.rules strong { color: var(--primary-2); }

@media (max-width: 860px) {
  .cols-3, .cols-4 { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 520px) {
  .cols-3, .cols-4 { grid-template-columns: 1fr; }
}
</style>
