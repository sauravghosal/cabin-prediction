<template>
  <v-calendar
    v-if="data"
    :from-date="date"
    :attributes="attrs"
    :columns="$screens({ default: 1, md: 2, lg: 5 })"
    :rows="$screens({ default: 1, md: 2 })"
    :is-expanded="$screens({ default: true, lg: false })"
  />
  <p v-if="!data">No Data Available</p>
</template>

<script>
export default {
  name: "CalendarView",
  props: {
    startDate: {
      type: Date || null,
      required: true,
    },
    data: {
      type: String,
      required: true,
    },
  },
  // re-renders the calendar view on prop change
  computed: {
    attrs: function() {
      return this.buildDatasets(this.data, this.startDate);
    },
    date: function() {
      return this.startDate && new Date(this.startDate.getFullYear(), 0, 1);
    },
  },
  methods: {
    buildDatasets(data, startDate) {
      const attrs = [
        { key: "previously booked", highlight: "blue", dates: [] },
        { key: "new booking", highlight: "green", dates: [] },
        { key: "cancelation", highlight: "red", dates: [] },
      ];
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
