<template>
  <v-calendar
    :attributes="attrs"
    :columns="$screens({ default: 1, lg: 6 })"
    :rows="$screens({ default: 1, lg: 2 })"
    :is-expanded="$screens({ default: true, lg: false })"
  />
</template>

<script>
export default {
  name: "CalendarView",
  props: {
    startDate: {
      type: Date,
      required: true,
    },
    data: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      attrs: this.buildDatasets(),
    };
  },
  methods: {
    buildDatasets() {
      const attrs = [
        { key: "previously booked", highlight: "blue", dates: [] },
        { key: "new booking", highlight: "green", dates: [] },
        { key: "cancelation", highlight: "red", dates: [] },
      ];
      const data = this.data;
      const startDate = this.startDate;
      for (let i = 0; i < data.length; i++) {
        const d = new Date(startDate.getTime());
        switch (data[i]) {
          case "1":
            attrs[0].dates.push(
              new Date(d.setDate(startDate.getDate() - (data.length - i - 1)))
            );
            break;
          case "B":
            attrs[1].dates.push(
              new Date(d.setDate(startDate.getDate() - (data.length - i - 1)))
            );
            break;
          case "C":
            attrs[2].dates.push(
              new Date(d.setDate(startDate.getDate() - (data.length - i - 1)))
            );
        }
      }
      return attrs;
    },
  },
};
</script>
