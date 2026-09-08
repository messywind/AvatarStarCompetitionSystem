<script setup>
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { professions } from '../gameAssets'
import { MAX_SUBSTITUTES } from '../roster'
import Icon from '../components/Icon.vue'
import guardian from '../assets/game/guardian.webp'
import heavy from '../assets/game/heavy.webp'
import arena from '../assets/game/arena.webp'
import town from '../assets/game/sky-town.webp'

const auth = useAuthStore()
const steps = [
  { title: '创建选手账号', text: '注册并登录，用同一个账号管理参赛信息。' },
  { title: '选择赛事，提交报名', text: '整队出征或个人参赛，按赛事要求填写资料。' },
  { title: '等待审核，关注赛程', text: '在「我的报名」查看审核结果，公布后查看对阵。' },
]
</script>

<template>
  <div class="home container">
    <div class="lobby-heading"><span>欢迎来到赛事中心</span><span class="lobby-note"><span></span>百变兵团 · 玩家民间赛事</span></div>
    <section class="hero">
      <img :src="town" alt="" class="hero-landscape" fetchpriority="high" />
      <div class="hero-shade"></div>
      <div class="hero-copy">
        <div class="hero-label"><Icon name="trophy" :size="17" /><span>百变兵团 · 赛事</span></div>
        <h1>集结你的热爱<br /><span>下一战，一起赢。</span></h1>
        <p>熟悉的战场，全新的对手。<br />带上你的拿手职业，与伙伴一起踏上冠军之路。</p>
        <div class="hero-actions">
          <RouterLink :to="auth.isAuthenticated ? '/signup' : '/register'" class="hero-primary">{{ auth.isAuthenticated ? '立即报名参赛' : '注册并报名' }}<Icon name="arrow" :size="19" /></RouterLink>
          <RouterLink to="/browse" class="hero-secondary">探索赛事<Icon name="chevron" :size="16" /></RouterLink>
        </div>
      </div>
      <div class="hero-characters" aria-hidden="true"><img :src="heavy" class="hero-heavy" alt="" fetchpriority="high" /><img :src="guardian" class="hero-guardian" alt="" fetchpriority="high" /></div>
      <div class="hero-caption"><span class="caption-star">✦</span><span>熟悉的兵团，不变的热爱<small>AVATAR STAR / XUANHUA CUP</small></span></div>
      <div class="hero-bottom"><span><Icon name="users" :size="17" />战队 / 个人报名</span><span><Icon name="shield" :size="17" />四大职业集结</span><RouterLink to="/browse">查看赛事与对阵<Icon name="arrow" :size="16" /></RouterLink></div>
    </section>

    <section class="entry-strip">
      <div class="entry-symbol"><Icon name="flag" :size="25" /></div>
      <div class="entry-copy"><h2>你的下一场比赛，从这里开始</h2><p>查看赛事规则、报名时间和对阵安排，找到属于你的战场。</p></div>
      <RouterLink to="/browse" class="btn ghost">进入赛事浏览<Icon name="arrow" :size="17" /></RouterLink>
    </section>

    <section class="profession-section">
      <div class="section-heading"><div><h2>四大职业，各有所长</h2><p>找到你的战斗方式，也找到最默契的队友。</p></div><span class="section-note">阵容搭配，决定战场可能</span></div>
      <div class="profession-grid">
        <article v-for="prof in professions" :key="prof.name" class="profession" :style="{ '--profession-color': prof.color, '--profession-tint': prof.tint }">
          <div class="profession-copy"><span class="profession-en">{{ prof.en }}</span><h3>{{ prof.name }}</h3><p>{{ prof.description }}</p></div>
          <img :src="prof.image" :alt="`${prof.name}职业角色`" loading="lazy" />
          <span class="profession-watermark" aria-hidden="true">{{ prof.name }}</span>
        </article>
      </div>
    </section>

    <div class="guide-grid">
      <section class="registration-guide">
        <div class="section-heading"><div><h2>三步，准备出战</h2><p>从第一次集结，到正式踏上赛场。</p></div></div>
        <ol class="flow-list"><li v-for="(step, i) in steps" :key="step.title"><span class="flow-number">{{ i + 1 }}</span><div><h3>{{ step.title }}</h3><p>{{ step.text }}</p></div><Icon v-if="i === 2" name="flag" :size="22" /></li></ol>
        <RouterLink :to="auth.isAuthenticated ? '/signup' : '/register'" class="guide-link">{{ auth.isAuthenticated ? '前往报名' : '创建我的选手账号' }}<Icon name="arrow" :size="17" /></RouterLink>
      </section>
      <section class="rules-section">
        <div class="rules-image"><img :src="arena" alt="百变兵团占点战场" loading="lazy" /><span><Icon name="shield" :size="17" />出发前，确认你的阵容</span></div>
        <div class="rules-copy"><h2>组队参赛须知</h2><ul><li><strong>5 名正式队员</strong><span>替补最多 {{ MAX_SUBSTITUTES }} 人，完整填写选手称呼及职业。</span></li><li><strong>合理搭配四大职业</strong><span>每种职业 1–2 人；生化可由护卫或重装补位。</span></li><li><strong>提交后等待审核</strong><span>具体职业及参赛限制，以所选赛事规则为准。</span></li></ul><RouterLink to="/browse">查看具体赛事规则<Icon name="chevron" :size="16" /></RouterLink></div>
      </section>
    </div>
    <div class="home-signoff"><Icon name="star" :size="18" /><p>无论整队出征，还是独自奔赴，赛场上总有你的位置。</p><span>百变兵团 · 赛事</span></div>
  </div>
</template>

<style scoped>
.home { padding-top: 1.5rem; padding-bottom: 1rem; }
.lobby-heading { display: flex; justify-content: space-between; align-items: center; color: #566474; font-size: .8rem; margin-bottom: 1rem; }
.lobby-heading > span:first-child { font-weight: 600; color: var(--text); }
.lobby-note { display: flex; align-items: center; gap: .5rem; font-size: .74rem; }
.lobby-note > span { width: 6px; height: 6px; background: #438764; border-radius: 50%; }
.hero { min-height: 460px; background: #1d303f; border-radius: 12px; position: relative; overflow: hidden; isolation: isolate; color: #fff; }
.hero-landscape { position: absolute; inset: 0 0 0 auto; width: 80%; height: 100%; object-fit: cover; object-position: right center; opacity: .72; z-index: -3; }
.hero-shade { position: absolute; inset: 0; background: linear-gradient(90deg, #172b3b 10%, #172b3bf5 31%, #172b3b85 63%, #172b3b10), linear-gradient(0deg,#172330b3,transparent 55%); z-index: -2; }
.hero-copy { padding: 3rem 3.2rem 6.5rem; position: relative; z-index: 2; max-width: 610px; }
.hero-label { display: inline-flex; align-items: center; gap: .55rem; color: #ffc99f; font-weight: 600; font-size: .8rem; margin-bottom: 1.15rem; }
.hero h1 { font-size: clamp(2.3rem, 3.5vw, 3.45rem); font-weight: 850; line-height: 1.25; letter-spacing: -.035em; margin-bottom: 1.05rem; color: #fff; }
.hero h1 span { color: #ffab68; }
.hero-copy p { color: #c5d1dc; line-height: 1.9; font-size: .9rem; margin: 0; }
.hero-actions { display: flex; align-items: center; gap: 1.65rem; margin-top: 1.6rem; }
.hero-primary { display: inline-flex; align-items: center; gap: 1.6rem; min-height: 48px; padding: .75rem 1.25rem; border-radius: 6px; color: #172330; background: #ff914d; font-weight: 750; font-size: .9rem; transition: background .2s, transform .2s; }
.hero-primary:hover { background: #ffad79; text-decoration: none; transform: translateY(-2px); }
.hero-secondary { color: #eef4fa; font-weight: 550; font-size: .86rem; display: flex; align-items: center; gap: .4rem; }
.hero-characters { position: absolute; width: 54%; right: 1.3%; top: 18px; height: 390px; pointer-events: none; z-index: 1; }
.hero-characters img { position: absolute; object-fit: contain; filter: drop-shadow(0 12px 8px #07151b55); }
.hero-heavy { height: 335px; width: 340px; right: 0; top: 5px; transform: rotate(7deg); }
.hero-guardian { height: 380px; width: 330px; left: 0; bottom: 0; transform: rotate(-8deg); }
.hero-caption { display: flex; align-items: center; gap: .6rem; position: absolute; right: 3rem; bottom: 82px; color: #fff; font-size: .78rem; font-weight: 600; z-index: 2; text-shadow: 0 1px 3px #172330; }
.caption-star { font-size: 2rem; color: #ffcf85; }
.hero-caption small { display: block; font-size: .55rem; color: #c4d2de; margin-top: .1rem; letter-spacing: .14em; }
.hero-bottom { position: absolute; bottom: 0; left: 0; right: 0; min-height: 56px; display: flex; align-items: center; gap: 2rem; padding: .8rem 3.2rem; background: #152432c7; border-top: 1px solid #ffffff1c; color: #c3d0dc; font-size: .78rem; z-index: 3; }
.hero-bottom span, .hero-bottom a { display: inline-flex; align-items: center; gap: .55rem; }
.hero-bottom .ui-icon { color: #efad75; }
.hero-bottom a { margin-left: auto; color: #e5edf5; }
.entry-strip { display: flex; align-items: center; gap: 1rem; padding: 1.4rem 1.6rem; margin-top: 1rem; background: #fff; border-radius: 10px; border: 1px solid var(--border); }
.entry-symbol { display: grid; place-items: center; width: 48px; height: 48px; color: var(--primary); background: var(--accent-soft); border-radius: 8px; flex: none; }
.entry-copy h2 { font-size: 1.02rem; margin: 0 0 .25rem; }
.entry-copy p { color: var(--muted); margin: 0; font-size: .8rem; }
.entry-strip .btn { margin-left: auto; flex: none; font-size: .82rem; gap: 1.2rem; }
.profession-section { margin-top: 2.6rem; }
.section-heading { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin-bottom: 1.2rem; }
.section-heading h2 { margin: 0 0 .4rem; font-size: 1.4rem; }
.section-heading p { margin: 0; font-size: .82rem; color: var(--muted); }
.section-note { font-size: .75rem; color: var(--muted); }
.profession-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: .85rem; }
.profession { position: relative; min-height: 220px; border-radius: 9px; overflow: hidden; isolation: isolate; background: var(--profession-tint); }
.profession-copy { position: relative; z-index: 2; padding: 1.15rem 1.25rem; }
.profession-en { font-size: .58rem; font-weight: 750; letter-spacing: .1em; color: var(--profession-color); }
.profession h3 { font-size: 1.65rem; margin: .25rem 0; color: var(--profession-color); }
.profession p { position: absolute; top: 176px; left: 1.25rem; font-size: .69rem; font-weight: 550; white-space: nowrap; color: var(--profession-color); margin: 0; }
.profession img { position: absolute; height: 184px; width: 170px; object-fit: contain; right: -15px; top: 24px; z-index: 1; transition: transform .35s var(--ease-out); }
.profession:hover img { transform: translateY(-5px) rotate(3deg); }
.profession-watermark { position: absolute; bottom: 16px; left: 13px; z-index: -1; font-weight: 900; font-size: 4.5rem; line-height: 1; color: var(--profession-color); opacity: .07; }
.guide-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 3rem 0 0; }
.registration-guide { padding: 1.5rem 1.6rem; background: #fff; border: 1px solid var(--border); border-radius: 10px; }
.flow-list { list-style: none; padding: 0; margin: 1.5rem 0 .8rem; }
.flow-list li { display: flex; align-items: flex-start; gap: 1rem; position: relative; padding-bottom: 1.5rem; }
.flow-list li:not(:last-child)::before { content: ''; position: absolute; left: 16px; top: 37px; bottom: 6px; width: 1px; background: var(--border); }
.flow-number { width: 33px; height: 33px; flex: none; display: grid; place-items: center; background: #eef1f5; color: #4a5c6e; font-weight: 750; border-radius: 50%; font-size: .83rem; }
.flow-list li:last-child .flow-number { color: var(--primary); background: var(--accent-soft); }
.flow-list h3 { font-size: .94rem; margin: .2rem 0 .3rem; }
.flow-list p { font-size: .79rem; color: var(--muted); margin: 0; }
.flow-list .ui-icon { color: var(--primary); margin: .35rem 0 0 auto; }
.guide-link { display: flex; align-items: center; justify-content: space-between; border-top: 1px solid var(--border); padding-top: 1rem; font-size: .85rem; font-weight: 650; }
.rules-section { overflow: hidden; border-radius: 10px; background: #fff; border: 1px solid var(--border); }
.rules-image { height: 130px; position: relative; overflow: hidden; }
.rules-image img { width: 100%; height: 100%; object-fit: cover; object-position: center 45%; }
.rules-image::after { content: ''; position: absolute; inset: 0; background: linear-gradient(0deg, #132536b3, transparent); }
.rules-image > span { position: absolute; left: 1.5rem; bottom: 1rem; z-index: 1; color: #fff; display: flex; align-items: center; gap: .5rem; font-size: .8rem; font-weight: 600; }
.rules-copy { padding: 1.3rem 1.5rem; }
.rules-copy h2 { font-size: 1.08rem; margin-bottom: .8rem; }
.rules-copy ul { padding: 0; list-style: none; margin: 0; }
.rules-copy li { display: flex; flex-direction: column; margin-bottom: .75rem; font-size: .78rem; }
.rules-copy strong { font-size: .82rem; font-weight: 650; margin-bottom: .15rem; }
.rules-copy li span { color: var(--muted); }
.rules-copy a { font-size: .8rem; font-weight: 650; display: inline-flex; align-items: center; gap: .4rem; margin-top: .25rem; }
.home-signoff { display: flex; align-items: center; justify-content: center; gap: .7rem; padding: 1.6rem 0; margin-top: 1rem; color: #657282; font-size: .75rem; }
.home-signoff .ui-icon { color: var(--primary); }
.home-signoff span { margin-left: auto; font-size: .68rem; }
@media(min-width:1100px) { .hero-characters { animation: assemble .7s var(--ease-out); } }
@keyframes assemble { from { transform: translateX(20px); } to { transform: none; } }
@media(max-width:1050px) { .hero-copy { padding-left: 2.2rem; max-width: 540px; } .hero-characters { right: -4%; width: 52%; } .hero-heavy { width: 290px; height: 300px; } .hero-guardian { width: 265px; height: 330px; bottom: 25px; } .hero-caption { right: 2rem; } .profession-grid { grid-template-columns: repeat(2, minmax(0,1fr)); } .profession { min-height: 205px; } .profession img { right: 8px; height: 200px; width: 190px; top: 5px; } .profession p { top: 166px; } .guide-grid { gap: 1rem; } }
@media(max-width:760px) {
 .home { padding-top: 1rem; } .lobby-heading { font-size: .73rem; } .lobby-note { font-size: .65rem; } .lobby-note > span { display: none; }
 .hero { min-height: 600px; } .hero-copy { padding: 1.8rem 1.6rem 0; max-width: 100%; } .hero h1 { font-size: 2.35rem; } .hero-label { margin-bottom: .85rem; } .hero-copy p { font-size: .82rem; }
 .hero-landscape { width: 100%; opacity: .6; object-position: 70% center; } .hero-shade { background: linear-gradient(180deg, #172b3bf5 28%, #172b3b55 70%, #172b3b); }
 .hero-characters { width: 83%; height: 275px; top: auto; bottom: 53px; right: 4%; } .hero-heavy { width: 205px; height: 230px; right: -12px; top: 20px; } .hero-guardian { width: 195px; height: 260px; left: 2px; bottom: 0; }
 .hero-caption { display: none; } .hero-actions { gap: 1.25rem; margin-top: 1.2rem; } .hero-primary { min-height: 45px; padding: .7rem 1rem; gap: 1rem; }
 .hero-bottom { padding: .8rem 1.3rem; gap: .85rem; min-height: 54px; font-size: .67rem; } .hero-bottom a { font-size: 0; gap: 0; } .hero-bottom a .ui-icon { width: 20px; height: 20px; }
 .entry-strip { flex-wrap: wrap; padding: 1.15rem; gap: .8rem; } .entry-copy { flex: 1; } .entry-copy h2 { font-size: .91rem; } .entry-copy p { font-size: .74rem; } .entry-strip .btn { width: 100%; margin: .2rem 0 0; justify-content: space-between; } .entry-symbol { width: 40px; height: 40px; }
 .section-note { display: none; } .section-heading h2 { font-size: 1.25rem; } .profession-section { margin-top: 2rem; } .profession-grid { gap: .7rem; } .profession { min-height: 240px; } .profession-copy { padding: .9rem; } .profession h3 { font-size: 1.4rem; } .profession-en { font-size: .54rem; } .profession img { width: 135px; height: 155px; top: 54px; right: -4px; } .profession p { left: .9rem; top: 210px; font-size: .62rem; } .profession-watermark { font-size: 3rem; bottom: 35px; }
 .guide-grid { grid-template-columns: 1fr; margin-top: 2rem; } .registration-guide { padding: 1.3rem; } .rules-image { height: 160px; } .home-signoff { font-size: .7rem; align-items: flex-start; } .home-signoff span { display: none; } .home-signoff p { margin: 0; } .lobby-note { max-width: 145px; text-align: right; }
}
@media(max-width:360px) { .hero-copy { padding-left: 1.1rem; padding-right: 1.1rem; } .hero h1 { font-size: 2.05rem; } .hero-secondary { font-size: .8rem; } .hero-actions { gap: 1rem; } .hero-characters { width: 96%; right: 0; } .hero-bottom { padding-inline: .85rem; } .profession img { width: 120px; } }
</style>
