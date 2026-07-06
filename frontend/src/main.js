import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router.js'
import App from './App.vue'
import './style.css'

// PrimeVue + tema
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

// Componentes PrimeVue utilizados
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'
import Badge from 'primevue/badge'
import Tooltip from 'primevue/tooltip'
import Steps from 'primevue/steps'
import Timeline from 'primevue/timeline'
import Card from 'primevue/card'
import Chip from 'primevue/chip'
import ConfirmDialog from 'primevue/confirmdialog'
import ConfirmationService from 'primevue/confirmationservice'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ToastService)
app.use(ConfirmationService)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: 'html.dark',  // Aplica cuando <html class="dark">
      cssLayer: false,
    }
  },
  pt: {
    button: {
      root: { class: 'transition-all duration-200' }
    }
  }
})

// Registro global de componentes
app.component('PButton', Button)
app.component('PDataTable', DataTable)
app.component('PColumn', Column)
app.component('PTag', Tag)
app.component('PInputText', InputText)
app.component('PSelect', Select)
app.component('PDialog', Dialog)
app.component('PTextarea', Textarea)
app.component('PToast', Toast)
app.component('PProgressBar', ProgressBar)
app.component('PSkeleton', Skeleton)
app.component('PBadge', Badge)
app.component('PSteps', Steps)
app.component('PTimeline', Timeline)
app.component('PCard', Card)
app.component('PChip', Chip)
app.component('PConfirmDialog', ConfirmDialog)

app.directive('tooltip', Tooltip)

app.mount('#app')
