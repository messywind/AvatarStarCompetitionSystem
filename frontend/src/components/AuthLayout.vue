<script setup>
import { RouterLink } from 'vue-router'
import Icon from './Icon.vue'
import guardian from '../assets/game/guardian.webp'
import assault from '../assets/game/assault.webp'
import town from '../assets/game/sky-town.webp'
defineProps({ register: Boolean })
</script>
<template>
  <div class="container auth-page">
    <RouterLink to="/" class="auth-back"><span>←</span> 返回赛事大厅</RouterLink>
    <div class="auth-shell">
      <aside class="auth-story">
        <img :src="town" class="story-bg" alt="" />
        <div class="story-copy"><span class="story-label"><Icon name="trophy" :size="18" />赛事 · 选手通行证</span><h2>{{ register ? '新的战友，' : '好久不见，' }}<br />{{ register ? '一起出发。' : '欢迎归队。' }}</h2><p>每一场精彩的对局，<br />都从一次热爱的集结开始。</p></div>
        <div class="story-characters" aria-hidden="true"><img :src="assault" alt="" /><img :src="guardian" alt="" /></div>
        <div class="story-foot"><Icon name="shield" :size="16" />一个账号，开启你的参赛旅程</div>
      </aside>
      <section class="auth-form"><slot /></section>
    </div>
    <p class="auth-note">百变兵团民间赛事报名平台 · 战队与个人均可参赛</p>
  </div>
</template>
<style scoped>
.auth-page { max-width: 1040px; padding-top: 2.2rem; }
.auth-back { display: inline-flex; align-items: center; gap: .5rem; margin-bottom: 1.3rem; color: var(--muted); font-size: .82rem; }
.auth-back span { font-size: 1.2rem; }
.auth-shell { display: grid; grid-template-columns: 1fr 1fr; min-height: 566px; border-radius: 12px; overflow: hidden; background: #fff; border: 1px solid var(--border); }
.auth-story { position: relative; isolation: isolate; background: var(--dark); overflow: hidden; color: #fff; }
.story-bg { position: absolute; inset: auto 0 0; width: 100%; height: 100%; object-fit: cover; opacity: .4; z-index: -2; }
.auth-story::after { content: ''; position: absolute; inset: 0; background: linear-gradient(180deg,#172330 20%,#17233044 74%,#172330); z-index: -1; }
.story-copy { padding: 2.5rem 2.5rem 0; position: relative; z-index: 2; }
.story-label { color: #efb484; display: flex; gap: .55rem; align-items: center; font-size: .77rem; }
.story-copy h2 { color: #fff; font-size: 2.5rem; margin: 1.5rem 0 1rem; line-height: 1.3; font-weight: 800; }
.story-copy p { color: #b7c6d5; font-size: .85rem; line-height: 1.9; }
.story-characters { position: absolute; bottom: 40px; height: 270px; width: 100%; }
.story-characters img { position: absolute; height: 250px; width: 220px; object-fit: contain; bottom: 0; left: 5px; transform: rotate(-9deg); }
.story-characters img + img { left: auto; right: 2px; height: 280px; width: 240px; transform: rotate(7deg); }
.story-foot { position: absolute; left: 0; right: 0; bottom: 0; padding: 1rem 1.6rem; display: flex; align-items: center; gap: .6rem; font-size: .73rem; color: #b6c6d3; background: #172330b8; border-top: 1px solid #ffffff17; }
.auth-form { padding: 3rem 2.8rem 2.2rem; align-self: center; }
.auth-form :deep(h1) { font-size: 1.75rem; margin: 0 0 .7rem; }
.auth-form :deep(.auth-intro) { font-size: .83rem; color: var(--muted); margin: 0 0 1.8rem; }
.auth-form :deep(.field) { margin-bottom: 1.15rem; }
.auth-form :deep(input) { min-height: 47px; background: #fafbfc; }
.auth-form :deep(input:focus) { background: #fff; }
.auth-form :deep(.btn) { min-height: 47px; margin-top: .5rem; }
.auth-form :deep(.switch) { margin: 1.5rem 0 0; border-top: 1px solid var(--border); padding-top: 1.2rem; font-size: .82rem; text-align: center; }
.auth-form :deep(.switch a) { font-weight: 650; margin-left: .3rem; }
.auth-note { text-align: center; color: var(--muted); font-size: .74rem; margin-top: 1.4rem; }
@media(max-width:760px) { .auth-page { max-width: 560px; padding-top: 1.2rem; } .auth-shell { grid-template-columns: 1fr; } .auth-story { min-height: 174px; } .story-copy { padding: 1.35rem 1.5rem; } .story-label { font-size: .67rem; } .story-copy h2 { font-size: 1.6rem; margin: .8rem 0 0; } .story-copy p, .story-foot { display: none; } .story-characters { height: 160px; right: -15px; width: 51%; bottom: -12px; } .story-characters img { height: 145px; width: 135px; } .story-characters img + img { height: 170px; width: 150px; right: -5px; } .auth-form { padding: 1.8rem 1.5rem; } .auth-form :deep(h1) { font-size: 1.5rem; } }
@media(max-width:370px) { .story-characters img:first-child { display: none; } }
</style>
