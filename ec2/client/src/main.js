import { createApp } from "vue";
import App from "./App.vue";
import VCalendar from "v-calendar";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { library } from "@fortawesome/fontawesome-svg-core";
import { faCalendarAlt } from "@fortawesome/free-solid-svg-icons";
import easySpinner from "vue-easy-spinner";

library.add(faCalendarAlt);

const app = createApp(App);
app.use(VCalendar, {});
app.component("font-awesome-icon", FontAwesomeIcon);
app.use(easySpinner, {
  prefix: "easy",
});

app.mount("#app");
