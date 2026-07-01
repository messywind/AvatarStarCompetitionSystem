<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import bgBattle from '../assets/bg-battle.jpg'
import bgTown from '../assets/bg-town.jpg'

const auth = useAuthStore()

const professions = [
  { name: '突击', desc: '高机动强火力先锋', key: '突击' },
  { name: '生化', desc: '毒液侵蚀，控场压制', key: '生化' },
  { name: '重装', desc: '重火力压制机甲', key: '重装' },
  { name: '护卫', desc: '前排肉盾稳固防线', key: '护卫' },
]
</script>

<template>
  <section class="hero" :style="{ backgroundImage: `url(${bgBattle})` }">
    <div class="hero-overlay"></div>
    <div class="hero-inner">
      <p class="kicker">AVATAR STAR · 官方赛事</p>
      <h1 class="hero-title">百变兵团 <span>选花杯</span></h1>
      <p class="hero-sub">
        组建你的五人战队，覆盖突击 · 生化 · 重装 · 护卫四大职业，踏上通往冠军的对阵之路。
      </p>
      <div class="hero-cta">
        <RouterLink v-if="auth.isAuthenticated" to="/signup" class="link-cta">立即报名 ›</RouterLink>
        <RouterLink v-else to="/register" class="link-cta">注册并报名 ›</RouterLink>
        <RouterLink to="/browse" class="link-cta ghost">查看赛事对阵 ›</RouterLink>
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
        <span class="prof-bar" :style="{ background: `var(--prof-${p.key})` }"></span>
        <span class="prof-tag" :class="'prof-' + p.key">
          <span class="dot" :style="{ background: `var(--prof-${p.key})` }"></span>{{ p.name }}
        </span>
        <p class="muted">{{ p.desc }}</p>
      </div>
    </div>
  </div>

  <section class="showcase" :style="{ backgroundImage: `url(${bgTown})` }">
    <div class="showcase-inner">
      <h2>集结你的战队</h2>
      <p>从小镇到战场，每一位选手都是胜利的关键。</p>
    </div>
  </section>

  <div class="container">
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
  min-height: 64vh;
  display: flex;
  align-items: flex-end;
  background-size: cover;
  background-position: center 30%;
  overflow: hidden;
}
.hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0) 35%, rgba(0, 0, 0, 0.55) 100%);
}
.hero-inner {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  width: 100%;
  padding: 0 1.5rem 3.5rem;
  color: #fff;
}
.kicker { letter-spacing: 3px; color: #fff; font-weight: 600; font-size: 0.78rem; margin: 0 0 0.6rem; opacity: 0.9; }
.hero-title { font-size: clamp(2.6rem, 6vw, 4.4rem); line-height: 1.05; letter-spacing: -0.02em; text-shadow: 0 2px 30px rgba(0, 0, 0, 0.4); }
.hero-title span {
  background: linear-gradient(135deg, #ffd479, var(--accent));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { max-width: 560px; color: rgba(255, 255, 255, 0.92); font-size: 1.1rem; line-height: 1.55; text-shadow: 0 1px 12px rgba(0, 0, 0, 0.5); }
.hero-cta { margin-top: 1.4rem; display: flex; gap: 1.6rem; flex-wrap: wrap; }
.link-cta { color: #fff; font-size: 1.05rem; font-weight: 500; }
.link-cta:hover { text-decoration: none; opacity: 0.85; }
.link-cta.ghost { color: #ffd479; }

.cols-3 { grid-template-columns: repeat(3, 1fr); }
.cols-4 { grid-template-columns: repeat(4, 1fr); }
.steps { margin-top: 2rem; }
.step-no { font-size: 1.5rem; font-weight: 700; color: var(--muted); opacity: 0.7; margin-bottom: 0.3rem; }

.section-title { margin: 3rem 0 1.2rem; }
.prof-card { position: relative; overflow: hidden; }
.prof-card p { margin: 0.5rem 0 0; }
.prof-bar { position: absolute; left: 0; top: 0; bottom: 0; width: 4px; }
.prof-tag { display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 700; font-size: 1.15rem; }
.prof-tag .dot { width: 10px; height: 10px; border-radius: 50%; }

.showcase {
  margin: 3.5rem 0 0;
  min-height: 320px;
  background-size: cover;
  background-position: center;
  display: flex; align-items: center; justify-content: center;
  position: relative;
}
.showcase::before { content: ''; position: absolute; inset: 0; background: rgba(255, 255, 255, 0.35); }
.showcase-inner { position: relative; text-align: center; color: var(--text); }
.showcase-inner h2 { font-size: clamp(1.8rem, 4vw, 2.6rem); text-shadow: 0 1px 20px rgba(255, 255, 255, 0.6); }
.showcase-inner p { color: #1d1d1f; font-size: 1.05rem; }

.rules { margin-top: 3rem; }
.rules ul { margin: 0.5rem 0 0; padding-left: 1.2rem; line-height: 2; color: var(--text); }
.rules strong { color: var(--primary); }

@media (max-width: 860px) {
  .cols-3, .cols-4 { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 520px) {
  .cols-3, .cols-4 { grid-template-columns: 1fr; }
}
</style>
