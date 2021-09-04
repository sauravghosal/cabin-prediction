<template>
  <div class="content">
    <div class="nav">
      <h2>GhosalRE Data Vis</h2>
    </div>
    <div class="occupancy-deltas">
      <h3>Occupancy Deltas</h3>
      <div class="user-input">
        <label for="cabin-selection">Select a cabin</label>
        <select
          v-model="selectedCabin"
          class="cabin-selection"
          :value="selectedCabin"
        >
          <option
            v-for="cabin in cabins"
            :value="cabin.value"
            :key="cabin.value"
          >
            {{ cabin.text }}
          </option>
        </select>
        <label class="date-label" for="date">Select Date</label>
        <v-date-picker
          v-model="date"
          :update-on-input="false"
          class="date-picker"
        >
          <template v-slot="{ inputValue, inputEvents }">
            <input
              class="date-selection"
              :value="inputValue"
              v-on="inputEvents"
            />
          </template>
        </v-date-picker>
      </div>
      <div class="calendar">
        <easy-spinner
          v-if="loading"
          color="#2196f3"
          size="75"
          type="circular"
        />
        <calendar-view v-if="!loading" :data="calendarData" :startDate="date" />
      </div>
    </div>
    <div class="occupancy"></div>
  </div>
</template>

<script>
import CalendarView from "../components/CalendarView.vue";
import axios from "axios";

export default {
  components: { CalendarView },
  name: "Home",
  data() {
    return {
      loading: true,
      selectedCabin: "",
      date: new Date(),
      calendarData: "",
      cabins: [],
    };
  },
  async mounted() {
    try {
      const cabins = await this.getAllCabins();
      this.cabins = cabins["cabins"].map((cabin) => {
        return { text: cabin, value: cabin };
      });
      this.selectedCabin = cabins["cabins"][0];
      const cabinOccupancyDiff = await this.getOccupancyDiff(
        this.selectedCabin
      );
      this.calendarData =
        cabinOccupancyDiff["occupancy"][this.getFormattedDate(this.date)];
      this.loading = false;
    } catch (err) {
      console.error(err);
      this.loading = false;
    }
  },

  // adjusting the displayed calendar based on user input
  // TODO: refactor code -> add it into function?
  watch: {
    selectedCabin: async function(cabinName) {
      try {
        this.loading = true;
        const cabinOccupancyDiff = await this.getOccupancyDiff(
          cabinName,
          this.date
        );
        this.calendarData =
          cabinOccupancyDiff["occupancy"][this.getFormattedDate(this.date)];
        this.loading = false;
      } catch (err) {
        console.error(err);
        setTimeout(() => (this.loading = false), 1000);
      }
    },
    date: async function(newDate) {
      try {
        this.loading = true;
        const cabinOccupancyDiff = await this.getOccupancyDiff(
          this.selectedCabin,
          newDate
        );
        this.loading = false;
        this.calendarData =
          cabinOccupancyDiff["occupancy"][this.getFormattedDate(this.date)];
      } catch (err) {
        console.error(err);
        setTimeout(() => (this.loading = false), 1000);
      }
    },
  },
  methods: {
    getFormattedDate: function(date) {
      let year = date.getFullYear();
      let month = (1 + date.getMonth()).toString();
      month = month.length > 1 ? month : "0" + month;
      let day = date.getDate().toString();
      day = day.length > 1 ? day : "0" + day;
      return month + "-" + day + "-" + year;
    },
    getAllCabins: async function() {
      return axios.get("/api/cabins").then((res) => res.data);
    },
    getOccupancyDiff: async function(cabinName, date) {
      console.log(
        `Finding occupancy deltas for cabin ${cabinName} and date ${this.getFormattedDate(
          date
        )}`
      );
      return axios
        .get("/api/occupancy-delta", {
          params: {
            cabin: cabinName,
            start_date: this.getFormattedDate(date),
            end_date: this.getFormattedDate(date),
          },
        })
        .then((res) => res.data);
    },
  },
};
</script>

<style scoped>
.content {
  width: 100%;
  margin: 0;
}
.nav {
  background-color: #333;
  color: white;
  padding: 10px;
  display: flex;
}

.nav h2 {
  margin: 0 0 0 5px;
}

.nav h2:hover {
  cursor: pointer;
}

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-left: 20px;
  padding-right: 20px;
}

.user-input {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2px;
  margin: 10px;
}

@media screen and (max-width: 750px) {
  .user-input {
    flex-direction: column;
  }
  .cabin-selection,
  .date-picker,
  .date-selection {
    width: 100%;
  }
}

.cabin-selection,
.date-picker {
  margin: 5px 0px 3px 5px;
  min-width: 100px;
}

.date-label {
  margin-left: 20px;
  margin-right: 5px;
}
</style>
