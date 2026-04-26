import { createRouter, createWebHistory } from "vue-router";
import ChatView from "./views/ChatView.vue";
import PoolView from "./views/PoolView.vue";
import ReportView from "./views/ReportView.vue";
import ProfileView from "./views/ProfileView.vue";
import HoldingsView from "./views/HoldingsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chat",
    },
    {
      path: "/chat",
      component: ChatView,
    },
    {
      path: "/pool",
      component: PoolView,
    },
    {
      path: "/holdings",
      component: HoldingsView,
    },
    {
      path: "/report",
      component: ReportView,
    },
    {
      path: "/profile",
      component: ProfileView,
    },
  ],
});

