import { createApp } from "vue";
import { inject } from "@vercel/analytics";
import { injectSpeedInsights } from "@vercel/speed-insights";
import Clarity from "@microsoft/clarity";
import App from "./App.vue";
import router from "./router";
import "./styles.css";

createApp(App).use(router).mount("#app");

inject();
injectSpeedInsights();
Clarity.init("yray5qx1st");
