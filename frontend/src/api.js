import axios from 'axios'

const api = axios.create({
  baseURL: 'https://dataepis.uandina.pe:49267/bot-posgrado/api',
  timeout: 30000,
})

export default api
