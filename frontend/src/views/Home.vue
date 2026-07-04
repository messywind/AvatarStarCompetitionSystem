<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import bgBattle from '../assets/bg-battle.jpg'
import bgTown from '../assets/bg-town.jpg'

const auth = useAuthStore()
</script>

<template>
  <div class="home">
    <section class="hero" :style="{ backgroundImage: `url(${bgBattle})` }">
      <div class="hero-overlay"></div>
      <div class="hero-inner">
        <p class="kicker">AVATAR STAR · 民间赛事</p>
        <h1 class="hero-title">百变兵团 <span>选花杯</span></h1>
        <p class="hero-sub">
          组建你的五人战队，或直接以个人身份报名，覆盖突击 · 生化 · 重装 · 护卫四大职业，踏上通往冠军的对阵之路。
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
        <div class="card step-card" style="--i: 0">
          <div class="step-no">01</div>
          <h3>注册账号</h3>
          <p class="muted">创建你的选手账号，一分钟即可完成。</p>
        </div>
        <div class="card step-card" style="--i: 1">
          <div class="step-no">02</div>
          <h3>提交报名</h3>
          <p class="muted">可选择战队报名或个人报名，按对应方式填写资料。</p>
        </div>
        <div class="card step-card" style="--i: 2">
          <div class="step-no">03</div>
          <h3>审核晋级</h3>
          <p class="muted">通过审核后进入对阵图，逐轮争夺冠军。</p>
        </div>
      </div>

      <section class="registration-flow">
        <div class="flow-heading">
          <h2>注册报名流程</h2>
          <p class="muted">从创建账号到通过审核，队长按流程提交资料即可完成报名。</p>
        </div>
        <div class="flow-list">
          <div class="flow-item" style="--i: 0">
            <span class="flow-no">1</span>
            <div>
              <h3>创建选手账号</h3>
              <p class="muted">使用常用账号注册并登录系统，后续报名、查询审核结果都在同一账号下完成。</p>
            </div>
          </div>
          <div class="flow-item" style="--i: 1">
            <span class="flow-no">2</span>
            <div>
              <h3>填写战队信息</h3>
              <p class="muted">选择战队报名时，队长填写战队名称、联系方式、正式队员与替补名单。</p>
            </div>
          </div>
          <div class="flow-item" style="--i: 2">
            <span class="flow-no">3</span>
            <div>
              <h3>提交资料并等待审核</h3>
              <p class="muted">个人报名填写称呼与职业，确认资料无误后提交，管理员会统一审核。</p>
            </div>
          </div>
          <div class="flow-item" style="--i: 3">
            <span class="flow-no">4</span>
            <div>
              <h3>通过后查看赛程</h3>
              <p class="muted">审核通过的队伍会进入赛事浏览页，可查看对阵图并关注后续比赛安排。</p>
            </div>
          </div>
        </div>
      </section>
    </div>

    <section class="showcase" :style="{ backgroundImage: `url(${bgTown})` }">
      <div class="showcase-inner">
        <h2>集结你的战队</h2>
        <p>从小镇到战场，无论是整队出征还是个人报名，每一位选手都是胜利的关键。</p>
      </div>
    </section>

    <div class="container">
      <div class="panel rules">
        <h2>组队规则</h2>
        <ul>
          <li>每支战队 <strong>正式队员严格为 5 人</strong>，替补人数不限。</li>
          <li>四大职业 <strong>每种至少 1 人、至多 2 人</strong>；若没有生化，可换成一个非突击职业（护卫 / 重装）。</li>
          <li>报名提交后需经 <strong>管理员审核</strong>，通过后方可出现在赛事浏览页。</li>
        </ul>
      </div>
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
  isolation: isolate;
  animation: hero-focus 0.8s var(--ease-soft) both;
}
.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: inherit;
  background-size: cover;
  background-position: center 30%;
  z-index: -2;
  transform: scale(1.035);
  animation: hero-drift 12s var(--ease-soft) both;
}
.hero-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0) 35%, rgba(0, 0, 0, 0.55) 100%);
  z-index: -1;
}
.hero-inner {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  width: 100%;
  padding: 0 1.5rem 3.5rem;
  color: #fff;
}
.kicker,
.hero-title,
.hero-sub,
.hero-cta {
  animation: hero-copy-in 0.58s var(--ease-soft) both;
}
.hero-title { animation-delay: 0.08s; }
.hero-sub { animation-delay: 0.16s; }
.hero-cta { animation-delay: 0.23s; }
.kicker { letter-spacing: 3px; color: #fff; font-weight: 600; font-size: 0.78rem; margin: 0 0 0.6rem; opacity: 0.9; }
.hero-title { font-size: clamp(2.6rem, 6vw, 4.4rem); line-height: 1.05; letter-spacing: -0.02em; text-shadow: 0 2px 30px rgba(0, 0, 0, 0.4); }
.hero-title span {
  background: linear-gradient(135deg, #ffd479, var(--accent));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { max-width: 560px; color: rgba(255, 255, 255, 0.92); font-size: 1.1rem; line-height: 1.55; text-shadow: 0 1px 12px rgba(0, 0, 0, 0.5); }
.hero-cta { margin-top: 1.4rem; display: flex; gap: 1.6rem; flex-wrap: wrap; }
.link-cta {
  color: #fff;
  font-size: 1.05rem;
  font-weight: 500;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  transition: opacity 0.18s var(--ease-out), transform 0.18s var(--ease-out);
}
.link-cta:hover { text-decoration: none; opacity: 0.85; }
.link-cta:active { transform: translateY(1px) scale(0.98); }
.link-cta.ghost { color: #ffd479; }

.cols-3 { grid-template-columns: repeat(3, 1fr); }
.cols-4 { grid-template-columns: repeat(4, 1fr); }
.steps { margin-top: 2rem; }
.step-card {
  animation: card-rise 0.42s var(--ease-soft) both;
  animation-delay: calc(var(--i) * 70ms);
}
.step-no { font-size: 1.5rem; font-weight: 700; color: var(--muted); opacity: 0.7; margin-bottom: 0.3rem; }

.section-title { margin: 3rem 0 1.2rem; }
.registration-flow { margin-top: 3rem; }
.flow-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-bottom: 1.2rem;
}
.flow-heading p {
  max-width: 520px;
  margin: 0 0 0.7rem;
  line-height: 1.65;
}
.flow-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}
.flow-item {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 1rem;
  align-items: start;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  animation: card-rise 0.42s var(--ease-soft) both;
  animation-delay: calc(var(--i) * 55ms);
  transition: border-color 0.18s var(--ease-out), box-shadow 0.18s var(--ease-out), transform 0.18s var(--ease-out);
}
.flow-item:hover {
  border-color: rgba(0, 113, 227, 0.26);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.flow-no {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 113, 227, 0.1);
  color: var(--primary);
  font-weight: 700;
  font-size: 1.05rem;
}
.flow-item h3 { margin-bottom: 0.35rem; }
.flow-item p { margin: 0; line-height: 1.65; }

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

@keyframes hero-focus {
  from { background-position: center 22%; }
  to { background-position: center 30%; }
}

@keyframes hero-drift {
  from { transform: scale(1.06); }
  to { transform: scale(1.015); }
}

@keyframes hero-copy-in {
  from {
    opacity: 0;
    transform: translateY(14px);
    filter: blur(5px);
  }
  to {
    opacity: 1;
    transform: none;
    filter: none;
  }
}

@keyframes card-rise {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (max-width: 860px) {
  .cols-3, .cols-4 { grid-template-columns: 1fr 1fr; }
  .flow-heading { display: block; }
  .flow-list { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .hero {
    min-height: 72vh;
    background-position: 52% center;
  }
  .hero-inner {
    padding: 0 1rem 2.4rem;
  }
  .kicker {
    letter-spacing: 1.8px;
    font-size: 0.72rem;
  }
  .hero-title {
    font-size: clamp(2.35rem, 13vw, 3.25rem);
  }
  .hero-sub {
    font-size: 1rem;
  }
  .hero-cta {
    gap: 0.8rem;
  }
  .link-cta {
    width: 100%;
    justify-content: center;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.14);
    backdrop-filter: blur(10px);
  }
  .link-cta.ghost {
    color: #fff0c2;
  }
  .cols-3, .cols-4 { grid-template-columns: 1fr; }
  .flow-item {
    grid-template-columns: 36px 1fr;
    padding: 1rem;
  }
  .flow-no {
    width: 36px;
    height: 36px;
  }
  .showcase {
    min-height: 240px;
    margin-top: 2.5rem;
  }
  .rules {
    margin-top: 1.5rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero,
  .hero::after,
  .kicker,
  .hero-title,
  .hero-sub,
  .hero-cta,
  .step-card,
  .flow-item {
    animation: none;
  }
}
</style>
