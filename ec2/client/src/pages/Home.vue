<template>
<ui-rangepicker></ui-rangepicker>
<line-graph-chart />
</template>

<script>
import LineGraphChart from '../components/LineGraphChart.vue'
export default {
  components: { LineGraphChart },
  name: 'Home',
}
</script>