import heavy from './assets/game/heavy.webp'
import guardian from './assets/game/guardian.webp'
import assault from './assets/game/assault.webp'
import bio from './assets/game/bio.webp'
export const professions = [
  { name: '突击', en: 'ASSAULT', image: assault, color: '#7945b8', tint: '#eee9f6', description: '灵活突进，抢占先机' },
  { name: '生化', en: 'BIOCHEMIST', image: bio, color: '#a9384c', tint: '#f7e9eb', description: '掌控战局，支援全场' },
  { name: '重装', en: 'GUNNER', image: heavy, color: '#87600c', tint: '#f5edda', description: '重火压制，正面出击' },
  { name: '护卫', en: 'GUARDIAN', image: guardian, color: '#15698f', tint: '#e3eff4', description: '坚守阵线，并肩作战' },
]
export const professionImage = Object.fromEntries(professions.map(p => [p.name, p.image]))
