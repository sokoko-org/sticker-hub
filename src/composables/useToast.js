import { readonly, ref } from "vue";

const message = ref("");
let timer;

export function useToast() {
  const showToast = (text) => {
    message.value = text;
    window.clearTimeout(timer);
    timer = window.setTimeout(() => {
      message.value = "";
    }, 1800);
  };

  return { message: readonly(message), showToast };
}
